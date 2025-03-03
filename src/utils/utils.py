import json
import re

class Utils:
    @staticmethod
    def jsonl2list(file_path):
        data_list = []
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                data_list.append(json.loads(line.strip()))
        return data_list

    @staticmethod
    def txt2str(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
        
    @staticmethod
    def planning_syntax_check(planning):
        func_name = ''
        arguments = {}
        try:
            planning = json.loads(planning)
            func_name = planning['name']
            arguments = planning['parameters']
            return func_name, arguments
        except:
            pass
        try:
            for sentence in str(planning).split('.'):
                if '(' in sentence:
                    planning = sentence.replace("\n", "").replace(" ", "")
        except Exception:
            pass

        func_names = ["moveto", "pick", "place", "polish", "unlock", "unscrew", "unwrap", "foldsheet"]
        signals = ["endPlanning", "LoAError", "LoSError", "LoLError", "LoOError"]
        args_dict = {
            "moveto": ['name', 'robot', 'position'], 
            "pick": ["robot", "name"], 
            "place": ["robot", "position"], 
            "polish":["robot", "name"], 
            "unlock": ["robot", "name"], 
            "unscrew": ["robot", "name"], 
            "unwrap": ["robot", "name"],
            "foldsheet": ["robot", "name"], 
            "endplanning": [], 
            "LoAError": [], 
            "LoSError": [], 
            "LoLError": [], 
            "LoOError": []
            }
        try:
            func_name = planning.split("(")[0].replace("\n", "").replace("`", "").replace("json", "").replace("\"", "")

            if func_name in signals and planning.split("(")[1] == ")":
                return func_name, {}
            
            if func_name not in func_names:
                return "Analyze error. Illegal planning syntax", {}

            for token in planning.split("(")[1].replace(" ", "").split(")")[0].split(","):
                if token[:3] == 'ro_':
                    arguments["robot"] = token
                elif token[:3] == 'obj' or token[:3] == 'non':
                    arguments["name"] = token
                elif token[:3] == 'pos' and token[-1] != 'x':
                    arguments["position"] = token
                else:
                    return "Analyze error. Illegal planning syntax", {}
                
            if set(arguments.keys()) != set(args_dict[func_name]):
                return "Analyze error. Illegal planning syntax", {}
        except Exception:
            return "Analyze error. Illegal planning syntax", {}
        
        return func_name, arguments
        
    @staticmethod
    def output_to_jsonl(data, args):
        with open(args.resource_path + f"test_{args.model_name.split('/')[-1]}_MultiPlan+.jsonl", 'a', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False) + '\n')

    @staticmethod
    def update_state(description, env, history, robot_object, func_name, args):
        description['Planning'] = history
        description['Environment'] = env
        if func_name == 'pick':
            robot_object[args['robot']] = args['name']
        if func_name == 'place':
            robot_object[args['robot']] = None
        
        return description, robot_object
                
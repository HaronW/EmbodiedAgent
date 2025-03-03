import json
from src.agent.client import Planner
from src.utils.tools import Tools
from src.utils.utils import Utils
import time
# import openai
import argparse

class PlanningExecutor:
    def __init__(self, client):
        self.client = client
        self.max_retries = 3

    def process_single_prompt(self, query):
        """Process single user prompt with step-by-step execution"""
        history = []
        step_count = 0
        should_continue = True
        description = json.loads(query[1]['content'].replace("\'", "\""))
        robot_object = {}
        for i in range(len(description['Environment']['Robot'])):
            robot_object[description['Environment']['Robot'][i]['name']] = None
        func_names = ["moveto", "pick", "place", "polish", "unlock", "unscrew", "unwrap", "foldsheet", "endPlanning", "LoAError", "LoSError", "LoLError", "LoOError"]


        while should_continue and step_count < 15:
            query = str(description) + str(robot_object)
            response = self.client.get_response(query)

            if not response:
                try:
                    temp = response.replace("\n", "").strip()
                    temp = response.choices[0].message.content.replace("\n", "").strip()
                    for split_point in func_names:
                        if len(temp.split(split_point)) > 1:
                            temp = split_point + temp.split(split_point)[-1]
                except IndexError:
                    temp = response.choices[0].message.content

                func_name, args = Utils.planning_syntax_check(temp)
                if func_name == "Analyze error. Illegal planning syntax":
                    print(response.choices[0].message.content)
                    print("Analyze error. Illegal planning syntax")
                    history.append(response.choices[0].message.content)
                    description['Planning'] = history
                    return description
            elif type(response) is str:
                tool_call = response.choices[0].message.tool_calls[0]
                func_name, args = Utils.planning_syntax_check(response)
            else:
                tool_call = response.choices[0].message.tool_calls[0]
                tool_call = response.replace("\n", "")
                func_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
            
            # Execute action
            if func_name.lower() == 'endplanning':
                func_name = 'endPlanning'
            elif func_name.lower() == 'looerror':
                func_name = 'LoOError'
            elif func_name.lower() == 'loserror':
                func_name = 'LoSError'
            elif func_name.lower() == 'loaerror':
                func_name = 'LoAError'
            elif func_name.lower() == 'lolerror':
                func_name = 'LoLError'

            try:
                action_method = getattr(Tools, func_name) 
                env = action_method(robot_object, description['Environment'], **args)
            except TypeError as e:
                history.append("Illegal aruguments:" + response)
                description['Planning'] = history
                print("Illegal aruguments." )
                return description
            except AttributeError as e:
                history.append("Illegal skills:" + response)
                description['Planning'] = history
                print("Illegal skills.")
                return description

            if func_name.lower() == "endplanning":
                print("Termination signal received")
                history.append("endPlanning()")
                should_continue = False
            elif func_name == "LoAError" or func_name == "LoSError" or func_name == "LoLError" or func_name == "LoOError":
                print("Impractical error occured")
                history.append(f"{func_name}()")
                should_continue = False
            else:
                action = func_name + '(' + ', '.join([v for k,v in args.items() if k != 'env']) + ')'
                
                if env == "Argument error. Can not update environment.":
                    history.append("Argument Error:" + action)
                    description['Planning'] = history
                    print(history)
                    del a
                    return description
                else:
                    history.append(action)
            
            step_count += 1
            
            description, robot_object = Utils.update_state(description, env, history, robot_object, func_name, args)
            query = description
        
        return description

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='MultiPlan+')
    parser.add_argument('--model_name', default="", help='Name of the AI model to use')
    parser.add_argument('--api_key', default="", help='Api Key')
    parser.add_argument('--base_url', default="https://api.siliconflow.cn/v1", help='Url of online llm service')
    parser.add_argument('--resource_path', default="./resources/", help='Path to data samples file/directory')
    parser.add_argument('--local_model_path', required=False, help='Path to local llm')
    args = parser.parse_args()


    client = Planner(args)
    executor = PlanningExecutor(client)

    for idx, query in enumerate(client.data_samples):
        print(f"\nProcessing prompt #{idx+1}")
        data_entry = executor.process_single_prompt(query)
        data_entry['id'] = id
        Utils.output_to_jsonl(data_entry, args)
        print(data_entry)
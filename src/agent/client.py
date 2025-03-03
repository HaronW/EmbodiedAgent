import openai
from ..utils.utils import Utils
import transformers
import torch

class Planner:
    def __init__(self, args):
        self.args = args
        if self.args.local_model_path is None:
            self.client = openai.OpenAI(
                api_key=self.args.api_key,
                base_url=self.args.base_url
            )
        else:
            self.tokenizer = transformers.AutoTokenizer.from_pretrained(
                self.args.local_model_path,
                trust_remote_code=True
                )
            
            self.model = transformers.AutoModelForCausalLM.from_pretrained(
                self.args.local_model_path,
                trust_remote_code=True, 
                device_map='auto'
                )

        self.resource_path = self.args.resource_path
        self._load_resources()

    def _load_resources(self):
        self.tools = Utils.jsonl2list(f"{self.resource_path}skill.jsonl")
        self.system_prompt = Utils.txt2str(f"{self.resource_path}system_prompt.txt")
        self.data_samples = Utils.jsonl2list(f"{self.resource_path}test_MultiPlan+.jsonl")

    def get_response(self, message):
        messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": message}
                ]
        if self.args.local_model_path is None:
            
            return self.client.chat.completions.create(
                model=self.args.model_name,
                messages=messages,
                temperature=0.01,
                trust_remote_code=True,
                stream=False
            )
        else:
            formatted_input = self.tokenizer.apply_chat_template(messages, add_generation_prompt = True, tokenize=False)
            
    
            inputs = self.tokenizer(formatted_input, return_tensors="pt").to("cuda")
            with torch.no_grad():
                outputs = self.model.generate(**inputs, max_new_tokens=1024)
    
            action = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
    
            return action.split("assistant")[1].replace("\n", "")
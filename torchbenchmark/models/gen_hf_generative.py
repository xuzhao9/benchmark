import os
from pathlib import Path

class_models = [
    ('hf_GPT2', (4, 512), 1024, 'AutoConfig.from_pretrained("gpt2")', 'AutoModelForCausalLM'),
    ('hf_T5', (2, 1024), 2048, 'AutoConfig.from_pretrained("t5-small")', 'AutoModelForSeq2SeqLM'),
    ('hf_Bart', (4, 512), 512, 'AutoConfig.from_pretrained("facebook/bart-base")', 'AutoModelForSeq2SeqLM'),
    ('hf_Reformer', (8, 4096), 4096, 'ReformerConfig()', 'AutoModelForMaskedLM'),
    ('hf_BigBird', (2, 1024), 4096, 'BigBirdConfig(attention_type="block_sparse",)', 'AutoModelForMaskedLM'),
    ('hf_Albert', (8, 512), 512, 'AutoConfig.from_pretrained("albert-base-v2")', 'AutoModelForMaskedLM'),
    ('hf_DistilBert', (8, 512), 512, 'AutoConfig.from_pretrained("distilbert-base-uncased")', 'AutoModelForMaskedLM'),
    ('hf_Longformer', (2, 1024), 4096, 'AutoConfig.from_pretrained("allenai/longformer-base-4096")', 'AutoModelForMaskedLM'),
    ('hf_Bert', (4, 512), 512, 'BertConfig()', 'AutoModelForMaskedLM')
]
for name, input_shape, eval_length, config, model in class_models:
    folder = Path(name)
    if not os.path.isdir(folder):
        os.makedirs(folder)
    init_program = f"""
####################################
# Generated by gen_hf_generative.py#
####################################

import torch
import torch.optim as optim
import torchvision.models as models
from ...util.model import BenchmarkModel
from torchbenchmark.tasks import NLP
from transformers import *
from datasets import load_dataset

class Model(BenchmarkModel):
    task = NLP.LANGUAGE_MODELING

    def __init__(self, device=None, jit=False):
        super().__init__()
        self.device = device
        self.jit = jit

        torch.manual_seed(42)
        config = {config}
        self.model = {model}.from_config(config).to(device)
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.001)

        input_ids = torch.randint(0, config.vocab_size, {input_shape}).to(device)
        decoder_ids = torch.randint(0, config.vocab_size, {input_shape}).to(device)

        eval_context = torch.randint(0, config.vocab_size, (1, {eval_length})).to(device)

        self.train_inputs = {{'input_ids': input_ids, 'labels': decoder_ids}}
        self.eval_inputs = {{'input_ids': eval_context, {"'decoder_input_ids': eval_context" if model == 'AutoModelForSeq2SeqLM' else ''}}}

    def get_module(self):
        if self.jit:
            raise NotImplementedError()
        return self.model, self.eval_inputs

    def train(self, niter=3):
        if self.jit:
            raise NotImplementedError()
        self.model.train()
        for _ in range(niter):
            outputs = self.model(**self.train_inputs)
            loss = outputs.loss
            loss.backward()
            self.optimizer.step()

    def eval(self, niter=1):
        if self.jit:
            raise NotImplementedError()
        self.model.eval()
        with torch.no_grad():
            for _ in range(niter):
                out = self.model(**self.eval_inputs)


if __name__ == "__main__":
    import time
    m = Model(device="cuda")
    module, example_inputs = m.get_module()

    m.train(niter=1)
    torch.cuda.synchronize()

    begin = time.time()
    m.train(niter=1)
    torch.cuda.synchronize()
    print(time.time()-begin)

    begin = time.time()
    m.eval(niter=1)
    torch.cuda.synchronize()
    print(time.time()-begin)
    """
    with open(folder / '__init__.py', 'w') as f:
        f.write(init_program)
    with open(folder / 'install.py', 'w') as f:
        pip_install_str = """
import subprocess
import sys

def pip_install_requirements():
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', '-r', 'requirements.txt'])
if __name__ == '__main__':
    pip_install_requirements()
"""
        f.write(pip_install_str)

    with open(folder / 'requirements.txt', 'w') as f:
        f.write('transformers==4.5.0\n')
        f.write('sentencepiece\n')
        f.write('datasets\n')

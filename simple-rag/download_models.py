from transformers import AutoModel, AutoTokenizer

model_name = "BAAI/bge-small-en-v1.5"
local_dir = "../../local_model"

# Download and save the model and tokenizer
model = AutoModel.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)

model.save_pretrained(local_dir)
tokenizer.save_pretrained(local_dir)
from torch import nn
import pandas
from transformers import BertModel, BertConfig, AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
import pandas as pd
from torch.optim import Adam
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import torch
from torch.utils.data import Dataset, DataLoader

from input_manager import import_csv

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# class TraceDataset(Dataset):
#     def __init__(self, X, y, max_len=50):
#         self.X = X
#         self.y = y
#         self.max_len = max_len

#     def __len__(self):
#         return len(self.X)

#     def __getitem__(self, idx):
#         # Pad sequences so that all have the same length
#         x = self.X[idx]
#         x_padded = x + [0] * (self.max_len - len(x))  # Padding with zeros
#         return torch.tensor(x_padded, dtype=torch.long), torch.tensor(self.y[idx], dtype=torch.long)

# class TracePredictor(nn.Module):
#     def __init__(self, n_activities):
#         super().__init__()
#         config = BertConfig.from_pretrained('distilbert-base-uncased', num_labels=n_activities)
#         self.bert = BertModel(config)
#         self.classifier = nn.Linear(config.hidden_size, n_activities)

#     def forward(self, x):
#         # Pass input through BERT model to get contextualized embeddings
#         outputs = self.bert(input_ids=x)
#         # Use the representation of the last token for predicting the next activity
#         sequence_output = outputs.last_hidden_state[:, -1, :]
#         # Classifier to predict next activity from the processed token
#         logits = self.classifier(sequence_output)
#         return logits

# Load your dataset
data = import_csv('log1.csv')


# Assuming 'data' is your DataFrame and 'concept:name' is the column of interest
labels = pd.Series(data['concept:name'].unique(), dtype="string")
# Create a new Series with the additional element
additional_labels = pd.Series(["end"], dtype="string")
# Concatenate the original labels with the new element
labels = pd.concat([labels, additional_labels]).reset_index(drop=True)
# Add end activity
num_labels = labels.size
print(f"Number of unique labels: {num_labels}")

le = LabelEncoder()
le.fit(labels)

# Encode activities to a categorical integer value
data['concept:name'] = le.transform(data['concept:name'])
data["concept:name"] = data["concept:name"].astype(int)

# Preprocess data: Remove a couple of columns and drop duplicates
# TODO: Make this dynamic
data = data.drop(columns=['case_id', 'activity', 'timestamp', 'enabled_activities'])
print(data)

# Add next activity column to the DataFrame and fill it
data["next_activity"] = None
def fill_next_activity_column(group: pandas.Series) -> pandas.DataFrame:
    previous_index = None
    for index, row in group.iterrows():
        if previous_index is not None:
            group.at[previous_index, "next_activity"] = row["concept:name"]
        previous_index = index
    return group
data = data.groupby("case:concept:name", group_keys=False).apply(fill_next_activity_column)
# Fill None values with the number of unique labels as end activity
# TODO: How do we map this number to an actual activity?
data = data.fillna(num_labels - 1)

print(data)

test_split = 0.2
train_df, test_df = train_test_split(
    data,
    test_size=test_split,
)
print(f"Number of rows in training set: {len(train_df)}")
print(f"Number of rows in test set: {len(test_df)}")


label_columns = ["next_activity"]
rest_columns = [col for col in data.columns if col not in label_columns]

train_labels = train_df[label_columns].values.tolist()
train_labels = [label[0] for label in train_labels]
print("Train labels:", train_labels)
train_texts = train_df[rest_columns].values.tolist()
train_texts = [', '.join(map(str, item)) for item in train_texts]
print("Train texts:", train_texts)

test_labels = test_df[label_columns].values.tolist()
test_labels = [label[0] for label in test_labels]
print("Test labels:", test_labels)
test_texts = test_df[rest_columns].values.tolist()
test_texts = [', '.join(map(str, item)) for item in test_texts]
print("Test texts:", test_texts)

tokenizer = AutoTokenizer.from_pretrained('distilbert-base-uncased', do_lower_case=True)

train_encodings = tokenizer(train_texts, padding="max_length", truncation=True, max_length=512)
test_encodings = tokenizer(test_texts, padding="max_length", truncation=True, max_length=512)

class TextClassifierDataset(Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item["labels"] = torch.tensor(self.labels[idx])
        return item

train_dataset = TextClassifierDataset(train_encodings, train_labels)
eval_dataset = TextClassifierDataset(test_encodings, test_labels)

print(train_dataset.labels)
print(eval_dataset.labels)

model = AutoModelForSequenceClassification.from_pretrained(
    "distilbert-base-uncased",
    problem_type="multi_label_classification",
    num_labels=num_labels
)

training_arguments = TrainingArguments(
    output_dir=".",
    eval_strategy="epoch",
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,
    num_train_epochs=8,
    use_cpu=True
)

class MyTrainer(Trainer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)    

    def compute_loss(self, model, inputs, return_outputs=False):
        labels = inputs.pop("labels")
        outputs = model(**inputs)
        logits = outputs[0]
        loss = nn.CrossEntropyLoss()
        return (loss(logits, labels), outputs) if return_outputs else loss(logits, labels)

trainer = MyTrainer(
    model=model,
    args=training_arguments,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
)

trainer.train()

model.eval()

print("Log after training:", data)

# Add enabled activities to the log
data["enabled__activities"] = None

def fill_enabled_activities_column(group: pandas.Series) -> pandas.DataFrame:

    enabled_activities = None

    for index, row in group.iterrows():
        # Generate input instance
        input = row[rest_columns].values.tolist()
        input = ', '.join(map(str, input))
        print("Input", input)
        inputs = tokenizer(input, padding=True, truncation=True, return_tensors="pt")
        inputs = inputs.to(device)

        with torch.no_grad():
            outputs = model(**inputs)

        logits = outputs.logits
        # probabilities = torch.softmax(logits, dim=1)
        probabilities = torch.sigmoid(logits)  # Apply sigmoid to convert logits to probabilities
        print(probabilities)

        #TODO: Parametize cutoff bound
        high_prob_indices = (probabilities > 0.).nonzero(as_tuple=True)[1]
        string_labels = le.inverse_transform(high_prob_indices)
        print("String labels", string_labels)
        #TODO: Add artificial start activity for training
        if enabled_activities is not None:
            group.at[index, "enabled__activities"] = tuple(sorted(enabled_activities, key=str.lower))
        enabled_activities = string_labels
    return group

data = data.groupby("case:concept:name", group_keys=False).apply(fill_enabled_activities_column).reset_index()

# Reverse label column to strings again
data["concept:name"] = le.inverse_transform(data["concept:name"])
print(data)
    

# # Generate all prefixes of each trace and the corresponding next activity
# for trace in traces:
#     for i in range(1, len(trace)):
#         X.append(trace[:i])
#         y.append(trace[i])

# # Split the data into training and test sets
# X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# # Initialize model and set up training essentials
# n_activities = data['Activity_encoded'].nunique()
# model = TracePredictor(n_activities)
# optimizer = Adam(model.parameters(), lr=1e-5)
# criterion = nn.CrossEntropyLoss()

# # Instantiate DataLoader for handling batches of data
# train_dataset = TraceDataset(X_train, y_train)
# train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)

# # Training loop
# for epoch in range(10):
#     model.train()
#     for inputs, labels in train_loader:
#         optimizer.zero_grad()
#         outputs = model(inputs)
#         loss = criterion(outputs, labels)
#         loss.backward()
#         optimizer.step()
#     print(f'Epoch {epoch+1}, Loss: {loss.item()}')

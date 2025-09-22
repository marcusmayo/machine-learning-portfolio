#!/usr/bin/env python3
"""
Ultra-simple document indexer - Works with ONLY numpy!
"""
import os
import json
import glob
import numpy as np

print("🚀 Starting document indexer...")

# Create sample policies if none exist
def create_sample_policies():
    raw_dir = "data/raw"
    os.makedirs(raw_dir, exist_ok=True)
    
    # Create sample files
    with open(f"{raw_dir}/expense_policy.txt", "w") as f:
        f.write("""EXPENSE POLICY
Business travel: Hotels up to $200/night
Meals: Breakfast $15, Lunch $25, Dinner $40
Home office: $500/year budget
Gym memberships: NOT reimbursable unless part of wellness program
Internet: $50/month for remote workers""")
    
    with open(f"{raw_dir}/vacation_policy.txt", "w") as f:
        f.write("""VACATION POLICY
Year 1-2: 10 days per year
Year 3-5: 15 days per year
Year 6+: 20 days per year
Request 2 weeks in advance
Sick leave: 10 days per year""")
    
    with open(f"{raw_dir}/remote_policy.txt", "w") as f:
        f.write("""REMOTE WORK POLICY
Standard: 2 days per week
Full remote: needs director approval
Core hours: 10am-3pm
Must use VPN for company systems
Equipment: $500 first year setup""")
    
    print("✅ Created sample policy files")
    return raw_dir

# Read documents
def read_documents(folder):
    docs = []
    for file in glob.glob(f"{folder}/*.txt"):
        with open(file, 'r') as f:
            docs.append({
                'text': f.read(),
                'source': os.path.basename(file)
            })
    return docs

# Create chunks
def chunk_text(docs):
    chunks = []
    chunk_id = 0
    for doc in docs:
        words = doc['text'].split()
        for i in range(0, len(words), 40):
            chunk = ' '.join(words[i:i+50])
            chunks.append({
                'id': chunk_id,
                'text': chunk,
                'source': doc['source']
            })
            chunk_id += 1
    return chunks

# Simple embeddings
def create_embeddings(chunks):
    # Build vocabulary
    all_words = ' '.join([c['text'].lower() for c in chunks]).split()
    vocab = list(set(all_words))[:200]  # Limit vocab size
    
    # Create vectors
    embeddings = []
    for chunk in chunks:
        vec = np.zeros(len(vocab))
        for word in chunk['text'].lower().split():
            if word in vocab:
                vec[vocab.index(word)] = 1
        embeddings.append(vec)
    
    return np.array(embeddings), vocab

# Main
print("Creating sample data...")
data_dir = create_sample_policies()

print("Reading documents...")
docs = read_documents(data_dir)
print(f"✅ Read {len(docs)} documents")

print("Creating chunks...")
chunks = chunk_text(docs)
print(f"✅ Created {len(chunks)} chunks")

print("Creating embeddings...")
embeddings, vocab = create_embeddings(chunks)

# Save everything
print("Saving index...")
os.makedirs("index/faiss", exist_ok=True)

with open("index/faiss/chunks.json", "w") as f:
    json.dump(chunks, f)

np.save("index/faiss/embeddings.npy", embeddings)

with open("index/faiss/vocabulary.json", "w") as f:
    json.dump(vocab, f)

print("✅ SUCCESS! Index created!")
print(f"Files created in: index/faiss/")

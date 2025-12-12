"""
Script to add initial memory about Bharath to Mem0
"""
import os
from dotenv import load_dotenv
from mem0 import MemoryClient

load_dotenv()

# Initialize Mem0 client
mem0 = MemoryClient(api_key=os.getenv("MEM0_API_KEY"))

# Add initial memories about Bharath - multiple entries for better recall
memories = [
    # Educational background
    [
        {
            "role": "user",
            "content": "I studied at J.M.J School and completed my Intermediate at Sri Chaitanya in Vizag."
        },
        {
            "role": "assistant",
            "content": "Great! So you completed your schooling at J.M.J School and your Intermediate at Sri Chaitanya in Vizag."
        }
    ],
    # Current education
    [
        {
            "role": "user",
            "content": "I'm currently a B.Tech Final year student at Godavari Institute of Engineering and Technology, pursuing CSE (AIML) branch with a CGPA of 8.9."
        },
        {
            "role": "assistant",
            "content": "Impressive! You're in your final year of B.Tech at Godavari Institute of Engineering and Technology in CSE (AIML) with an excellent CGPA of 8.9."
        }
    ],
    # Professional work
    [
        {
            "role": "user",
            "content": "My name is Bharath Munakala and I'm a GenAI Developer currently working on AI Agents, Voice Agents, Video Agents, and RAG."
        },
        {
            "role": "assistant",
            "content": "Nice to meet you, Bharath Munakala! You're working as a GenAI Developer specializing in AI Agents, Voice Agents, Video Agents, and RAG systems."
        }
    ],
    # Personal interests
    [
        {
            "role": "user",
            "content": "I'm a foodie and I'm mostly interested in fighter jets and Mahabharata warriors."
        },
        {
            "role": "assistant",
            "content": "That's a fascinating combination of interests! You love food, fighter jets, and Mahabharata warriors."
        }
    ]
]

# Add all memories to Mem0 for user "samantha"
total_memories = 0
for idx, messages in enumerate(memories, 1):
    result = mem0.add(messages, user_id="samantha")
    count = len(result.get('results', []))
    total_memories += count
    print(f"✅ Memory set {idx} added: {count} memories")

print(f"\n🎉 Total: {total_memories} memories added successfully!")
print("\nYou can now chat with the agent and it will remember all this information!")


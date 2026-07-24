import os

path = os.path.join(
    os.path.dirname(__file__), '..', 'venv', 'Lib', 'site-packages',
    'ragas', 'llms', 'base.py'
)
path = os.path.abspath(path)
print('Patching:', path)

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old1 = 'from langchain_community.chat_models.vertexai import ChatVertexAI'
new1 = 'try:\n    from langchain_community.chat_models.vertexai import ChatVertexAI\nexcept ImportError:\n    class ChatVertexAI:\n        pass'

old2 = 'from langchain_community.llms import VertexAI'
new2 = 'try:\n    from langchain_community.llms import VertexAI\nexcept ImportError:\n    class VertexAI:\n        pass'

found1 = old1 in content
found2 = old2 in content
print('Found line 1:', found1)
print('Found line 2:', found2)

content = content.replace(old1, new1).replace(old2, new2)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print('File written.')
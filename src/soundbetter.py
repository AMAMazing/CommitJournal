from talktollm import talkto
from modules.mduse import combinemd, modfilewrite

prompt = combinemd(['src/prompt.md','src/output/focus.md'])

result = talkto('gemini',prompt)
modfilewrite(result,r'src\output\finished.md')

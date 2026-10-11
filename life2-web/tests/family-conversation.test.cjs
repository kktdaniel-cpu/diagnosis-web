const {test}=require('node:test');
const assert=require('node:assert/strict');
const {transformSync}=require('rolldown/experimental');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const source=transformSync('familyConversation.ts',fs.readFileSync(path.join(__dirname,'../src/familyConversation.ts'),'utf8')).code.replace('export function familyConversationBlockReason','exports.familyConversationBlockReason=function');
const context={exports:{}};vm.runInNewContext(source,context);
const reason=context.exports.familyConversationBlockReason;
test('selecting preferences alone cannot complete a conversation that did not happen',()=>{
 assert.match(reason({conversation_done:'NO',preference_topics:['CARE','DIGITAL_INFO']}),/저장하고 나중에/);
});
test('conversation and recorded preferences are both required',()=>{
 assert.ok(reason({}));assert.ok(reason({conversation_done:'YES',preference_topics:[]}));
 assert.equal(reason({conversation_done:'YES',preference_topics:['CARE']}),null);
});
test('malformed or unknown preference data cannot enable completion',()=>{
 assert.ok(reason({conversation_done:'YES',preference_topics:'CARE'}));
 assert.ok(reason({conversation_done:'YES',preference_topics:['UNKNOWN']}));
});

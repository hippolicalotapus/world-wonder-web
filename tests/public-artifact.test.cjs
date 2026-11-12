'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {assertPublicExport}=require('../src/public-catalogue.cjs');
const source={title:'Primary report',url:'https://example.org/report',publisher:'Example',accessed_on:'2026-11-12',source_type:'primary',rights_status:'link_only'};
const record=()=>({id:'test-1',title:'Illustrative test',collection:'Kindness',summary:'Not a real published story',claim_type:'documented_event',review_status:'published',sources:[{...source}]});
test('public export artifact passes strict privacy validation',()=>{
 const data=JSON.parse(fs.readFileSync(path.join(__dirname,'../public-catalogue.json'),'utf8'));
 assert.deepEqual(assertPublicExport(data),[]);
});
test('strict validation permits properly sanitized public record',()=>assert.equal(assertPublicExport([record()]).length,1));
test('rejects private contact and evidence fields in public file',()=>{
 for(const field of ['email','private_evidence','internal_review_history','submitter_identity']){
  assert.throws(()=>assertPublicExport([{...record(),[field]:'private'}]),/Unexpected public field/);
 }
});
test('rejects private source notes in public file',()=>{
 const r=record();r.sources[0].internal_notes='private';
 assert.throws(()=>assertPublicExport([r]),/Unexpected public source field/);
});
test('rejects drafts even when source is valid',()=>assert.throws(()=>assertPublicExport([{...record(),review_status:'draft'}])));
test('rejects pending source permissions',()=>{
 const r=record();r.sources[0].rights_status='permission_pending';
 assert.throws(()=>assertPublicExport([r]));
});

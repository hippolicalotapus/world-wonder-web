'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const {normalizePublicCatalog,searchPublicCatalog,CLAIM_LABELS} = require('../src/public-catalogue.cjs');
const sample = (id='one') => ({
 id,title:'Rescue story',collection:'Rescue & survival',summary:'Source-backed account',
 claim_type:'unverified_report',review_status:'published',private_evidence:'SECRET',
 sources:[{title:'Report',url:'https://example.org/report',publisher:'Example Press',
 accessed_on:'2026-11-12',source_type:'secondary',rights_status:'link_only',internal_notes:'SECRET'}]
});
test('sanitizes record and source private metadata',()=>{
 const out=normalizePublicCatalog([sample()])[0];
 assert.equal(out.private_evidence,undefined);
 assert.equal(out.sources[0].internal_notes,undefined);
 assert.equal(out.sources[0].url,'https://example.org/report');
});
test('rejects unpublished records',()=>assert.throws(()=>normalizePublicCatalog([{...sample(),review_status:'draft'}])));
test('rejects unsafe source links',()=>assert.throws(()=>normalizePublicCatalog([{...sample(),sources:[{...sample().sources[0],url:'javascript:alert(1)'}]}])));
test('rejects duplicate IDs',()=>assert.throws(()=>normalizePublicCatalog([sample(),sample()])));
test('requires primary source for documented events',()=>assert.throws(()=>normalizePublicCatalog([{...sample(),claim_type:'documented_event'}])));
test('rejects pending source rights',()=>assert.throws(()=>normalizePublicCatalog([{...sample(),sources:[{...sample().sources[0],rights_status:'permission_pending'}]}])));
test('search supports text, collection and evidence type',()=>{
 const items=normalizePublicCatalog([sample(),{...sample('two'),title:'Kindness account',collection:'Kindness & courage',claim_type:'first_person_testimony'}]);
 assert.equal(searchPublicCatalog(items,{query:'rescue'}).length,1);
 assert.equal(searchPublicCatalog(items,{collection:'Kindness & courage'}).length,1);
 assert.equal(searchPublicCatalog(items,{claimType:'first_person_testimony'}).length,1);
 assert.equal(searchPublicCatalog(items,{query:'not-found'}).length,0);
 assert.equal(CLAIM_LABELS.belief_or_tradition,'Belief or tradition');
});

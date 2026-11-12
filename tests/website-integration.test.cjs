'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const html=fs.readFileSync(path.join(__dirname,'../index.html'),'utf8');
const catalogue=JSON.parse(fs.readFileSync(path.join(__dirname,'../public-catalogue.json'),'utf8'));
test('website exposes a discoverable published-record section',()=>{
 for(const fragment of ['id="public-catalogue"','href="#public-catalogue"','id="record-search"','id="record-collection"','id="record-claim"','id="public-records"','id="record-status"']) assert.ok(html.includes(fragment),fragment);
});
test('website supports collection and evidence filtering',()=>{
 assert.match(html,/publicCollection\.value/);
 assert.match(html,/publicType\.value/);
 assert.match(html,/publicSearch\.value/);
});
test('website uses textContent and DOM nodes rather than record HTML injection',()=>{
 assert.match(html,/heading\.textContent=r\.title/);
 assert.match(html,/summary\.textContent=r\.summary/);
 assert.match(html,/a\.textContent='Source: '/);
});
test('website rejects drafts and pending-rights sources',()=>{
 assert.match(html,/r\.review_status==='published'/);
 assert.match(html,/s\.rights_status!=='permission_pending'/);
 assert.match(html,/\['http:','https:'\]/);
});
test('public catalogue fixture is valid and contains no fabricated records',()=>{
 assert.deepEqual(catalogue,[]);
});
test('existing subjects and membership preview remain available',()=>{
 for(const fragment of ['id="collections"','id="saved-count"','id="membership"','id="benefits"','id="standards"']) assert.ok(html.includes(fragment),fragment);
});

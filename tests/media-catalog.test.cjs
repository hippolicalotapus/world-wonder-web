'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const records=require('../data/media-catalog.json');
const {validateMediaCatalog}=require('../src/media-validation.cjs');
test('media catalog conforms to schema',()=>assert.deepEqual(validateMediaCatalog(records),[]));
test('all imported media remain unreviewed until human verification',()=>assert.ok(records.every(r=>r.verificationStatus==='proposed')));
test('no external embeds without rights review',()=>assert.ok(records.every(r=>r.embedAllowed===false)));
test('all media have publisher and original source',()=>assert.ok(records.every(r=>r.publisher&&r.canonicalUrl.startsWith('https://'))));

'use strict';
const TYPES = new Set(['youtube','podcast','institutional-video','institutional-audio']);
const ROLES = new Set(['primary','secondary','commentary','entertainment']);
const STATUSES = new Set(['proposed','reviewing','reviewed','rejected']);
function safeUrl(input) {
  try { const url = new URL(input); return url.protocol === 'https:' && Boolean(url.hostname) && !url.username && !url.password; }
  catch { return false; }
}
function validateMedia(record) {
  const errors = [];
  if (!record || typeof record !== 'object' || Array.isArray(record)) return ['Media record must be an object'];
  for (const key of ['id','title','publisher','language','rightsNotes']) {
    if (typeof record[key] !== 'string' || !record[key].trim()) errors.push(key + ' required');
  }
  if (typeof record.id === 'string' && !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(record.id)) errors.push('id must be a lowercase slug');
  if (!TYPES.has(record.mediaType)) errors.push('Invalid mediaType');
  if (!safeUrl(record.canonicalUrl)) errors.push('Invalid canonicalUrl');
  if (!ROLES.has(record.evidenceRole)) errors.push('Invalid evidenceRole');
  if (!STATUSES.has(record.verificationStatus)) errors.push('Invalid verificationStatus');
  if (!Array.isArray(record.archiveEntryIds) || record.archiveEntryIds.some(x=>typeof x !== 'string' || !x.trim())) errors.push('archiveEntryIds must be an array of IDs');
  if (!Array.isArray(record.topics) || record.topics.some(x=>typeof x !== 'string' || !x.trim())) errors.push('topics must be an array of strings');
  if (typeof record.embedAllowed !== 'boolean') errors.push('embedAllowed must be boolean');
  if (record.verificationStatus === 'reviewed' && (!record.reviewer || !/^\d{4}-\d{2}-\d{2}$/.test(record.reviewedAt || '') || Number.isNaN(Date.parse(record.reviewedAt)))) errors.push('Reviewed records need reviewer and reviewedAt');
  if (record.mediaType === 'youtube' && safeUrl(record.canonicalUrl)) {
    const host = new URL(record.canonicalUrl).hostname.toLowerCase();
    if (!['youtube.com','www.youtube.com','m.youtube.com','youtu.be'].includes(host)) errors.push('YouTube records require a YouTube URL');
  }
  return errors;
}
function validateMediaCatalog(records) {
  if (!Array.isArray(records)) return ['Media catalog must be an array'];
  const errors=[]; const ids=new Set();
  records.forEach((record,i)=>{
    validateMedia(record).forEach(error=>errors.push('Record '+i+': '+error));
    if (record && ids.has(record.id)) errors.push('Duplicate media ID: '+record.id);
    if (record) ids.add(record.id);
  });
  return errors;
}
module.exports = {validateMedia,validateMediaCatalog};

'use strict';
/** Validation for research records. No entry is assumed true merely because it passes. */
const STATES = new Set(['proposed','researching','verified','published','corrected','withdrawn']);
const CLAIM_TYPES = new Set(['documented','reported','disputed','interpretation','unverified']);
function isUrl(value) { try { const u = new URL(value); return ['https:','http:'].includes(u.protocol); } catch { return false; } }
function validateEntry(entry) {
  const errors = [];
  if (!entry || typeof entry !== 'object' || Array.isArray(entry)) return ['Entry must be an object'];
  for (const field of ['id','title','category','summary']) {
    if (typeof entry[field] !== 'string' || !entry[field].trim()) errors.push(field + ' is required');
  }
  if (typeof entry.id === 'string' && !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(entry.id)) errors.push('id must be a lowercase slug');
  if (!STATES.has(entry.status)) errors.push('Invalid status');
  if (!CLAIM_TYPES.has(entry.claimType)) errors.push('Invalid claim type');
  if (!Array.isArray(entry.sources)) errors.push('sources must be an array');
  else entry.sources.forEach((source, i) => {
    if (!source || typeof source.title !== 'string' || !source.title.trim() || !isUrl(source.url)) errors.push('Invalid source at index ' + i);
  });
  if (entry.status === 'verified' || entry.status === 'published' || entry.status === 'corrected') {
    if (!entry.sources?.length) errors.push('Verified and published records need sources');
    if (!/^\\d{4}-\\d{2}-\\d{2}$/.test(entry.reviewedAt || '') || Number.isNaN(Date.parse(entry.reviewedAt))) errors.push('Valid reviewedAt date required');
    if (!entry.reviewer || typeof entry.reviewer !== 'string') errors.push('Reviewer required');
  }
  if (entry.status === 'published' && entry.claimType === 'unverified') errors.push('Unverified claim cannot be published as a factual entry');
  if (entry.images && (!Array.isArray(entry.images) || entry.images.some(img => !img || !isUrl(img.url) || !img.rights || !img.caption))) errors.push('Images require URL, rights and caption');
  return errors;
}
function validateCatalog(records) {
  if (!Array.isArray(records)) return ['Catalog must be an array'];
  const errors = []; const ids = new Set();
  records.forEach((record, i) => {
    validateEntry(record).forEach(error => errors.push('Entry ' + i + ': ' + error));
    if (record && ids.has(record.id)) errors.push('Duplicate id: ' + record.id);
    if (record) ids.add(record.id);
  });
  return errors;
}
module.exports = {validateEntry, validateCatalog};

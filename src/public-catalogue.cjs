'use strict';
/** Read-only discovery over the sanitized public export. Never accepts editorial drafts. */
const CLAIM_LABELS = Object.freeze({
  documented_event: 'Documented event',
  first_person_testimony: 'First-person testimony',
  belief_or_tradition: 'Belief or tradition',
  unverified_report: 'Unverified report'
});
const PUBLIC_FIELDS = ['id','title','collection','summary','claim_type','review_status','sources'];
const SOURCE_FIELDS = ['title','url','publisher','accessed_on','source_type','rights_status'];
function safeUrl(value) {
  if (typeof value !== 'string') return false;
  try { const u = new URL(value); return ['https:', 'http:'].includes(u.protocol) && !!u.hostname; }
  catch { return false; }
}
function normalizePublicCatalog(input) {
  if (!Array.isArray(input)) throw new TypeError('Catalogue must be an array');
  const ids = new Set();
  return input.map((record, index) => {
    if (!record || typeof record !== 'object' || Array.isArray(record) ||
        record.review_status !== 'published' ||
        !['id','title','collection','summary'].every(k => typeof record[k] === 'string' && record[k].trim()) ||
        !Object.hasOwn(CLAIM_LABELS, record.claim_type) ||
        !Array.isArray(record.sources) || !record.sources.length ||
        record.sources.some(s => !s || typeof s !== 'object' ||
          !['title','publisher'].every(k => typeof s[k] === 'string' && s[k].trim()) ||
          !safeUrl(s.url) || !/^\d{4}-\d{2}-\d{2}$/.test(s.accessed_on || '') ||
          !['primary','secondary','testimony'].includes(s.source_type) ||
          !['link_only','licensed','public_domain'].includes(s.rights_status))) {
      throw new TypeError('Invalid published record at index ' + index);
    }
    if (ids.has(record.id)) throw new TypeError('Duplicate public record id');
    ids.add(record.id);
    if (record.claim_type === 'documented_event' &&
        !record.sources.some(s => s.source_type === 'primary')) throw new TypeError('Documented event requires primary source');
    const clean = Object.fromEntries(PUBLIC_FIELDS.filter(k => k !== 'sources').map(k => [k, record[k]]));
    clean.sources = record.sources.map(s => Object.fromEntries(SOURCE_FIELDS.map(k => [k, s[k]])));
    return clean;
  });
}
function searchPublicCatalog(records, {query = '', collection = '', claimType = ''} = {}) {
  const needle = String(query).trim().toLocaleLowerCase();
  return records.filter(r =>
    (!collection || r.collection === collection) &&
    (!claimType || r.claim_type === claimType) &&
    (!needle || [r.title,r.summary,r.collection,...r.sources.map(s => s.publisher)]
      .some(v => v.toLocaleLowerCase().includes(needle)))
  ).sort((a,b) => a.title.localeCompare(b.title) || a.id.localeCompare(b.id));
}
module.exports = {CLAIM_LABELS, normalizePublicCatalog, searchPublicCatalog};

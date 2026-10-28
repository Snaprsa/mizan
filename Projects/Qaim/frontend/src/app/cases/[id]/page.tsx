'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import {
    getCase, listSources, addUrlSource, uploadPdfSource,
    startExtraction, listJobs, getComps, updateCompStatus,
    overrideField, getExportCSVUrl, getExportXLSXUrl,
} from '@/lib/api';
import type { Case, Source, ExtractionJob, Comparable, ExtractedField, Citation } from '@/types';

export default function CaseDetailPage() {
    const params = useParams();
    const caseId = params.id as string;

    const [caseData, setCaseData] = useState<Case | null>(null);
    const [sources, setSources] = useState<Source[]>([]);
    const [jobs, setJobs] = useState<ExtractionJob[]>([]);
    const [comps, setComps] = useState<Comparable[]>([]);
    const [loading, setLoading] = useState(true);

    // Input state
    const [urlsText, setUrlsText] = useState('');
    const [adding, setAdding] = useState(false);
    const [extracting, setExtracting] = useState(false);

    // Modal
    const [editModal, setEditModal] = useState<{ compId: string; field: string; current: string } | null>(null);
    const [editValue, setEditValue] = useState('');
    const [editReason, setEditReason] = useState('');
    const [citationModal, setCitationModal] = useState<Citation | null>(null);

    const loadAll = useCallback(async () => {
        try {
            const [c, s, j, co] = await Promise.all([
                getCase(caseId), listSources(caseId), listJobs(caseId), getComps(caseId),
            ]);
            setCaseData(c); setSources(s); setJobs(j); setComps(co);
        } catch (e) { console.error(e); }
        finally { setLoading(false); }
    }, [caseId]);

    useEffect(() => { loadAll(); }, [loadAll]);

    // ── Add multiple URLs at once ──
    async function handleAddUrls() {
        const urls = urlsText.split('\n').map(u => u.trim()).filter(u => u.length > 5);
        if (urls.length === 0) return;
        setAdding(true);
        try {
            for (const url of urls) {
                await addUrlSource(caseId, url);
            }
            setUrlsText('');
            await loadAll();
        } catch (e) { alert('Failed to add some URLs'); }
        finally { setAdding(false); }
    }

    // ── Upload PDF ──
    async function handlePdf(e: React.ChangeEvent<HTMLInputElement>) {
        const file = e.target.files?.[0];
        if (!file) return;
        setAdding(true);
        try {
            await uploadPdfSource(caseId, file);
            await loadAll();
        } catch (e) { alert('Upload failed'); }
        finally { setAdding(false); e.target.value = ''; }
    }

    // ── Extract all pending sources ──
    async function handleExtractAll() {
        const pending = sources.filter(s => !jobs.find(j => j.source_id === s.id));
        if (pending.length === 0) {
            alert('All sources already extracted');
            return;
        }
        setExtracting(true);
        try {
            for (const s of pending) {
                await startExtraction(caseId, s.id);
            }
            await loadAll();
        } catch (e) { alert('Some extractions failed'); }
        finally { setExtracting(false); }
    }

    // ── Override ──
    function openEdit(compId: string, field: string, current: string) {
        setEditModal({ compId, field, current });
        setEditValue(current || '');
        setEditReason('');
    }
    async function submitEdit(e: React.FormEvent) {
        e.preventDefault();
        if (!editModal || !editReason.trim()) return;
        try {
            await overrideField(editModal.compId, { field_name: editModal.field, new_value: editValue, reason: editReason });
            setEditModal(null);
            await loadAll();
        } catch (e) { alert('Override failed'); }
    }

    // ── Helpers ──
    function confClass(c: number) { return c >= 0.7 ? 'high' : c >= 0.4 ? 'med' : 'low'; }

    function findCitation(comp: Comparable, fieldName: string): Citation | undefined {
        return comp.extracted_fields?.find(f => f.field_name === fieldName)?.citation as Citation | undefined;
    }

    function findConfidence(comp: Comparable, fieldName: string): number | undefined {
        return comp.extracted_fields?.find(f => f.field_name === fieldName)?.confidence;
    }

    function getArea(comp: Comparable): string {
        const a = (comp.areas || []).find(a => a.area_type === 'land_area' || a.area_type === 'plot_area');
        return a ? `${a.normalized_value || a.raw_value}` : '—';
    }

    function reliabilityText(s: number) {
        return { 1: 'Manual', 2: 'Listing', 3: 'Broker', 4: 'Official', 5: 'Transaction' }[s] || `${s}`;
    }

    if (loading) return <div className="page"><div className="empty"><p>Loading...</p></div></div>;
    if (!caseData) return <div className="page"><div className="empty"><h3>Case not found</h3></div></div>;

    const pendingCount = sources.filter(s => !jobs.find(j => j.source_id === s.id)).length;

    return (
        <div className="page">
            {/* Header */}
            <div className="mb-8">
                <a href="/" style={{ fontSize: 12, color: 'var(--text-3)' }}>← Back to Cases</a>
            </div>
            <div className="row-between mb-24">
                <div>
                    <h1 className="page-title">{caseData.title}</h1>
                    {caseData.city && <span className="page-sub">📍 {caseData.city}</span>}
                </div>
                <div className="btn-group">
                    <a href={getExportCSVUrl(caseId)} className="btn btn-sm" download>📊 CSV</a>
                    <a href={getExportXLSXUrl(caseId)} className="btn btn-sm" download>📗 Excel</a>
                </div>
            </div>

            {/* ── ADD LINKS SECTION ── */}
            <div className="card mb-24">
                <div className="row-between mb-16">
                    <div className="card-title">Add Comparable Links</div>
                    <label className="btn btn-sm" style={{ cursor: 'pointer' }}>
                        📄 Upload PDF
                        <input type="file" accept=".pdf" onChange={handlePdf} style={{ display: 'none' }} />
                    </label>
                </div>
                <textarea
                    className="textarea mb-16"
                    value={urlsText}
                    onChange={e => setUrlsText(e.target.value)}
                    placeholder={"Paste one or more links, one per line:\nhttps://sa.aqar.fm/...\nhttps://sa.aqar.fm/...\nhttps://pasteah.com/..."}
                    rows={4}
                />
                <div className="row-between">
                    <span className="card-meta">
                        {sources.length} source{sources.length !== 1 ? 's' : ''} added
                        {pendingCount > 0 && ` · ${pendingCount} pending extraction`}
                    </span>
                    <div className="btn-group">
                        <button className="btn" onClick={handleAddUrls} disabled={adding || !urlsText.trim()}>
                            {adding ? 'Adding...' : '+ Add Links'}
                        </button>
                        {pendingCount > 0 && (
                            <button className="btn btn-blue" onClick={handleExtractAll} disabled={extracting}>
                                {extracting ? (<><span className="spinner" /> Extracting...</>) : `▶ Extract All (${pendingCount})`}
                            </button>
                        )}
                    </div>
                </div>
            </div>

            {/* ── SOURCES LIST ── */}
            {sources.length > 0 && (
                <div className="mb-24">
                    <div className="label mb-8">Sources</div>
                    <div className="table-container">
                        <table>
                            <thead>
                                <tr><th>Type</th><th>URL / File</th><th>Status</th><th></th></tr>
                            </thead>
                            <tbody>
                                {sources.map(s => {
                                    const job = jobs.find(j => j.source_id === s.id);
                                    return (
                                        <tr key={s.id}>
                                            <td><span className="badge badge-blue">{s.source_type.toUpperCase()}</span></td>
                                            <td style={{ maxWidth: 400, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                                {s.url ? <a href={s.url} target="_blank" rel="noopener">{s.url}</a> : s.filename || '—'}
                                            </td>
                                            <td>
                                                {job ? (
                                                    <span className={`badge ${job.status === 'completed' ? 'badge-green' : job.status === 'failed' ? 'badge-red' : 'badge-amber'}`}>
                                                        {job.status === 'completed' ? `✓ ${job.fields_extracted} fields` : job.status}
                                                    </span>
                                                ) : (
                                                    <span className="badge badge-muted">pending</span>
                                                )}
                                            </td>
                                            <td>
                                                {!job && (
                                                    <button className="btn btn-sm" onClick={async () => {
                                                        setExtracting(true);
                                                        try { await startExtraction(caseId, s.id); await loadAll(); } catch { } finally { setExtracting(false); }
                                                    }}>▶</button>
                                                )}
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* ── COMPS TABLE ── */}
            {comps.length > 0 && (
                <>
                    <div className="row-between mb-16">
                        <div className="label" style={{ margin: 0 }}>Comparables ({comps.length})</div>
                    </div>
                    <div className="table-container mb-24">
                        <table>
                            <thead>
                                <tr>
                                    <th>#</th>
                                    <th>Property</th>
                                    <th>District</th>
                                    <th>Type</th>
                                    <th>Evidence</th>
                                    <th>Price (SAR)</th>
                                    <th>Area (sqm)</th>
                                    <th>SAR/sqm</th>
                                    <th>Reliability</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {comps.map((c, i) => (
                                    <tr key={c.id} className={c.is_invalid ? 'invalid' : c.is_outlier ? 'outlier' : ''}>
                                        <td style={{ color: 'var(--text-3)' }}>{i + 1}</td>
                                        <td>
                                            <div style={{ fontWeight: 500, maxWidth: 200 }}>
                                                {c.property_title?.slice(0, 40) || 'Untitled'}
                                            </div>
                                            {c.source_url && (
                                                <a href={c.source_url} target="_blank" rel="noopener" style={{ fontSize: 11 }}>
                                                    source ↗
                                                </a>
                                            )}
                                        </td>
                                        <td>
                                            <FieldCell value={c.district || c.city || '—'} confidence={findConfidence(c, 'district') ?? findConfidence(c, 'city')}
                                                citation={findCitation(c, 'district') ?? findCitation(c, 'city')}
                                                onCite={setCitationModal}
                                                onEdit={() => openEdit(c.id, 'district', c.district || '')} />
                                        </td>
                                        <td>{c.property_subtype || c.property_category || '—'}</td>
                                        <td>
                                            <span className={`badge ${c.evidence_type === 'transaction' ? 'badge-green' : c.evidence_type === 'listing' ? 'badge-blue' : 'badge-muted'}`}>
                                                {c.evidence_type}
                                            </span>
                                        </td>
                                        <td>
                                            <FieldCell
                                                value={c.asking_price ? c.asking_price.toLocaleString() : c.transacted_price ? c.transacted_price.toLocaleString() : '—'}
                                                confidence={findConfidence(c, 'asking_price')}
                                                citation={findCitation(c, 'asking_price')}
                                                onCite={setCitationModal}
                                                onEdit={() => openEdit(c.id, 'asking_price', String(c.asking_price || c.transacted_price || ''))}
                                            />
                                        </td>
                                        <td>
                                            <FieldCell value={getArea(c)} confidence={findConfidence(c, 'land_area')}
                                                citation={findCitation(c, 'land_area')} onCite={setCitationModal}
                                                onEdit={() => openEdit(c.id, 'land_area', getArea(c))} />
                                        </td>
                                        <td style={{ fontWeight: 600, color: 'var(--blue)' }}>
                                            {c.price_per_sqm ? c.price_per_sqm.toLocaleString() : '—'}
                                        </td>
                                        <td>
                                            <span className={`badge ${c.reliability_score >= 4 ? 'badge-green' : c.reliability_score >= 3 ? 'badge-blue' : 'badge-amber'}`}>
                                                {reliabilityText(c.reliability_score)}
                                            </span>
                                        </td>
                                        <td>
                                            <div className="btn-group">
                                                <button className="btn btn-sm" onClick={() => openEdit(c.id, 'city', c.city || '')} title="Edit">✏️</button>
                                                <button className={`btn btn-sm ${c.is_invalid ? '' : 'btn-red'}`}
                                                    onClick={() => updateCompStatus(c.id, { is_invalid: !c.is_invalid }).then(loadAll)}
                                                    title={c.is_invalid ? 'Restore' : 'Mark Invalid'}>
                                                    {c.is_invalid ? '↩' : '✗'}
                                                </button>
                                                <button className="btn btn-sm"
                                                    onClick={() => updateCompStatus(c.id, { is_outlier: !c.is_outlier }).then(loadAll)}
                                                    title={c.is_outlier ? 'Unmark Outlier' : 'Mark Outlier'}
                                                    style={c.is_outlier ? { color: 'var(--amber)' } : {}}>
                                                    {c.is_outlier ? '★' : '☆'}
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </>
            )}

            {/* ── NO COMPS STATE ── */}
            {comps.length === 0 && sources.length > 0 && (
                <div className="empty mb-24">
                    <h3>No comparables yet</h3>
                    <p>Click "Extract All" above to process your sources.</p>
                </div>
            )}

            {/* ── OVERRIDE AUDIT LOG ── */}
            {comps.some(c => c.overrides?.length > 0) && (
                <div className="mb-24">
                    <div className="label mb-8">Override Audit Log</div>
                    <div className="table-container">
                        <table>
                            <thead><tr><th>Field</th><th>Old</th><th>New</th><th>Reason</th><th>By</th><th>When</th></tr></thead>
                            <tbody>
                                {comps.flatMap(c => (c.overrides || []).map(o => (
                                    <tr key={o.id}>
                                        <td><code style={{ fontSize: 11, color: 'var(--blue)' }}>{o.field_name}</code></td>
                                        <td style={{ color: 'var(--red)' }}>{o.old_value || '—'}</td>
                                        <td style={{ color: 'var(--green)' }}>{o.new_value || '—'}</td>
                                        <td>{o.reason}</td>
                                        <td className="card-meta">{o.overridden_by}</td>
                                        <td className="card-meta">{o.overridden_at ? new Date(o.overridden_at).toLocaleString() : '—'}</td>
                                    </tr>
                                )))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* ── EDIT MODAL ── */}
            {editModal && (
                <div className="overlay" onClick={() => setEditModal(null)}>
                    <div className="modal" onClick={e => e.stopPropagation()}>
                        <div className="modal-title">Edit: {editModal.field}</div>
                        <p style={{ fontSize: 12, color: 'var(--text-3)', marginBottom: 16 }}>Current: {editModal.current || '(empty)'}</p>
                        <form onSubmit={submitEdit}>
                            <div className="mb-16">
                                <label className="label">New Value</label>
                                <input className="input" value={editValue} onChange={e => setEditValue(e.target.value)} autoFocus />
                            </div>
                            <div className="mb-24">
                                <label className="label">Reason *</label>
                                <textarea className="textarea" value={editReason} onChange={e => setEditReason(e.target.value)}
                                    placeholder="Why is this value being changed?" required style={{ minHeight: 60 }} />
                            </div>
                            <div className="btn-group" style={{ justifyContent: 'flex-end' }}>
                                <button type="button" className="btn" onClick={() => setEditModal(null)}>Cancel</button>
                                <button type="submit" className="btn btn-blue">Save</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* ── CITATION MODAL ── */}
            {citationModal && (
                <div className="overlay" onClick={() => setCitationModal(null)}>
                    <div className="modal" onClick={e => e.stopPropagation()}>
                        <div className="modal-title">Source Citation</div>
                        <div className="cite-panel">
                            <div className="mb-16">
                                <div className="cite-label">Source</div>
                                <div className="cite-value">{citationModal.source_name || citationModal.source_id}</div>
                            </div>
                            {citationModal.snippet && (
                                <div className="mb-16">
                                    <div className="cite-label">Extracted Text</div>
                                    <div className="cite-snippet">{citationModal.snippet}</div>
                                </div>
                            )}
                            <div className="grid-2" style={{ gap: 12, marginBottom: 12 }}>
                                <div>
                                    <div className="cite-label">Extractor</div>
                                    <div className="cite-value">{citationModal.extractor_name} v{citationModal.extractor_version}</div>
                                </div>
                                <div>
                                    <div className="cite-label">Confidence</div>
                                    <div className="cite-value">{(citationModal.parse_confidence * 100).toFixed(0)}%</div>
                                </div>
                            </div>
                            {citationModal.locator?.bounding_hint && (
                                <div className="mb-16">
                                    <div className="cite-label">Location Hint</div>
                                    <div className="cite-value">{citationModal.locator.bounding_hint}</div>
                                </div>
                            )}
                            {citationModal.locator?.page_number && (
                                <div>
                                    <div className="cite-label">Page</div>
                                    <div className="cite-value">{citationModal.locator.page_number}</div>
                                </div>
                            )}
                        </div>
                        <div style={{ marginTop: 16, textAlign: 'right' }}>
                            <button className="btn" onClick={() => setCitationModal(null)}>Close</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

/** Inline field cell with confidence + citation link */
function FieldCell({ value, confidence, citation, onCite, onEdit }: {
    value: string; confidence?: number; citation?: Citation;
    onCite: (c: Citation) => void; onEdit?: () => void;
}) {
    return (
        <div>
            <span onClick={onEdit} style={{ cursor: onEdit ? 'pointer' : 'default' }}
                title={onEdit ? 'Click to edit' : undefined}>{value}</span>
            {confidence !== undefined && confidence > 0 && (
                <div className="conf">
                    <div className="conf-bar">
                        <div className={`conf-fill ${confidence >= 0.7 ? 'high' : confidence >= 0.4 ? 'med' : 'low'}`}
                            style={{ width: `${confidence * 100}%` }} />
                    </div>
                    {(confidence * 100).toFixed(0)}%
                </div>
            )}
            {citation && (
                <button className="source-btn" onClick={e => { e.stopPropagation(); onCite(citation); }}>
                    📎 source
                </button>
            )}
        </div>
    );
}

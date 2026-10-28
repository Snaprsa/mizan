'use client';

import { useState, useEffect } from 'react';
import { listCases, createCase } from '@/lib/api';
import type { Case } from '@/types';

export default function HomePage() {
    const [cases, setCases] = useState<Case[]>([]);
    const [loading, setLoading] = useState(true);
    const [showCreate, setShowCreate] = useState(false);
    const [title, setTitle] = useState('');
    const [city, setCity] = useState('Riyadh');
    const [creating, setCreating] = useState(false);

    useEffect(() => { load(); }, []);

    async function load() {
        try { setCases(await listCases()); } catch (e) { console.error(e); }
        finally { setLoading(false); }
    }

    async function handleCreate(e: React.FormEvent) {
        e.preventDefault();
        if (!title.trim()) return;
        setCreating(true);
        try {
            await createCase({ title, city });
            setTitle(''); setShowCreate(false);
            await load();
        } catch (e) { alert('Failed to create case'); }
        finally { setCreating(false); }
    }

    return (
        <div className="page">
            <div className="row-between mb-24">
                <div>
                    <h1 className="page-title">Cases</h1>
                    <p className="page-sub">Your valuation projects</p>
                </div>
                <button className="btn btn-blue" onClick={() => setShowCreate(true)}>
                    + New Case
                </button>
            </div>

            {loading ? (
                <div className="empty"><p>Loading...</p></div>
            ) : cases.length === 0 ? (
                <div className="empty">
                    <h3>No cases yet</h3>
                    <p>Create your first valuation case to start adding comparables.</p>
                    <button className="btn btn-blue" style={{ marginTop: 16 }} onClick={() => setShowCreate(true)}>
                        + New Case
                    </button>
                </div>
            ) : (
                <div className="grid-3">
                    {cases.map((c) => (
                        <a key={c.id} href={`/cases/${c.id}`} style={{ textDecoration: 'none', color: 'inherit' }}>
                            <div className="card card-clickable">
                                <div className="card-title">{c.title}</div>
                                {c.city && <div className="card-meta mb-8">📍 {c.city}</div>}
                                <div className="row" style={{ gap: 16 }}>
                                    <span className="card-meta">{c.source_count} source{c.source_count !== 1 ? 's' : ''}</span>
                                    <span className="card-meta">{c.comp_count} comp{c.comp_count !== 1 ? 's' : ''}</span>
                                </div>
                            </div>
                        </a>
                    ))}
                </div>
            )}

            {showCreate && (
                <div className="overlay" onClick={() => setShowCreate(false)}>
                    <div className="modal" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-title">New Valuation Case</div>
                        <form onSubmit={handleCreate}>
                            <div className="mb-16">
                                <label className="label">Case Title</label>
                                <input className="input" value={title} onChange={e => setTitle(e.target.value)}
                                    placeholder="e.g. Land in الملقا — Riyadh" required autoFocus />
                            </div>
                            <div className="mb-24">
                                <label className="label">City</label>
                                <select className="input" value={city} onChange={e => setCity(e.target.value)}>
                                    <option value="Riyadh">Riyadh</option>
                                    <option value="Jeddah">Jeddah</option>
                                    <option value="Dammam">Dammam</option>
                                    <option value="Makkah">Makkah</option>
                                    <option value="Madinah">Madinah</option>
                                    <option value="Khobar">Khobar</option>
                                    <option value="Other">Other</option>
                                </select>
                            </div>
                            <div className="btn-group" style={{ justifyContent: 'flex-end' }}>
                                <button type="button" className="btn" onClick={() => setShowCreate(false)}>Cancel</button>
                                <button type="submit" className="btn btn-blue" disabled={creating}>
                                    {creating ? 'Creating...' : 'Create'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}

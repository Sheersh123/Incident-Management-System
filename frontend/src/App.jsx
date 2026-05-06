import { useState, useEffect } from 'react';
import axios from 'axios';
import { AlertCircle, Clock, CheckCircle, Shield, Activity, ChevronRight, X, RefreshCw } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { formatDistanceToNow } from 'date-fns';

const API_BASE = "http://localhost:8000";

function App() {
  const [incidents, setIncidents] = useState([]);
  const [metrics, setMetrics] = useState({ signals_per_sec_avg_5s: 0 });
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [rawSignals, setRawSignals] = useState([]);
  const [showRcaForm, setShowRcaForm] = useState(false);
  const [statusMessage, setStatusMessage] = useState(null);
  const [rcaData, setRcaData] = useState({
    root_cause_category: 'SOFTWARE_BUG',
    fix_applied: '',
    prevention_steps: '',
    incident_start: '',
    incident_end: ''
  });

  const fetchIncidents = async () => {
    try {
      const res = await axios.get(`${API_BASE}/incidents/`);
      setIncidents(res.data);
    } catch (e) { console.error(e); }
  };

  const fetchMetrics = async () => {
    try {
      const res = await axios.get(`${API_BASE}/health`);
      setMetrics(res.data.metrics);
    } catch (e) { console.error(e); }
  };

  const fetchRawSignals = async (incidentId) => {
    try {
      const res = await axios.get(`${API_BASE}/incidents/${incidentId}/signals`);
      setRawSignals(res.data.signals || []);
    } catch (e) { 
      console.error(e);
      setRawSignals([]);
    }
  };

  useEffect(() => {
    fetchIncidents();
    fetchMetrics();
    const interval = setInterval(() => {
      fetchIncidents();
      fetchMetrics();
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (selectedIncident) {
      fetchRawSignals(selectedIncident.id);
    }
  }, [selectedIncident]);

  const handleUpdateStatus = async (incidentId, newStatus) => {
    try {
      await axios.patch(`${API_BASE}/incidents/${incidentId}/status?new_status=${newStatus}`);
      setStatusMessage({ type: 'success', text: `Status updated to ${newStatus}` });
      fetchIncidents();
      // Refresh selected incident
      const res = await axios.get(`${API_BASE}/incidents/${incidentId}`);
      setSelectedIncident(res.data);
    } catch (e) {
      setStatusMessage({ type: 'error', text: e.response?.data?.detail || 'Failed to update status' });
    }
    setTimeout(() => setStatusMessage(null), 4000);
  };

  const handleSubmitRca = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_BASE}/rca/`, {
        incident_id: selectedIncident.id,
        root_cause_category: rcaData.root_cause_category,
        fix_applied: rcaData.fix_applied,
        prevention_steps: rcaData.prevention_steps
      });
      setShowRcaForm(false);
      setSelectedIncident(null);
      setRcaData({ root_cause_category: 'SOFTWARE_BUG', fix_applied: '', prevention_steps: '', incident_start: '', incident_end: '' });
      setStatusMessage({ type: 'success', text: 'RCA submitted — incident CLOSED' });
      fetchIncidents();
    } catch (e) {
      setStatusMessage({ type: 'error', text: e.response?.data?.detail || 'RCA submission failed' });
    }
    setTimeout(() => setStatusMessage(null), 4000);
  };

  const getNextStatus = (current) => {
    const map = { OPEN: 'INVESTIGATING', INVESTIGATING: 'RESOLVED', RESOLVED: 'CLOSED' };
    return map[current] || null;
  };

  const statusColor = (s) => {
    const m = { OPEN: '#f87171', INVESTIGATING: '#fbbf24', RESOLVED: '#34d399', CLOSED: '#94a3b8' };
    return m[s] || '#94a3b8';
  };

  return (
    <div className="app-container">
      {/* Toast Message */}
      <AnimatePresence>
        {statusMessage && (
          <motion.div
            initial={{ opacity: 0, y: -30 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -30 }}
            style={{
              position: 'fixed', top: 20, right: 20, zIndex: 2000,
              padding: '12px 20px', borderRadius: 12,
              background: statusMessage.type === 'success' ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)',
              border: `1px solid ${statusMessage.type === 'success' ? '#10b981' : '#ef4444'}`,
              color: statusMessage.type === 'success' ? '#34d399' : '#f87171',
              fontSize: '0.875rem', fontWeight: 600
            }}
          >
            {statusMessage.text}
          </motion.div>
        )}
      </AnimatePresence>

      <header className="header">
        <div>
          <h1 style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <Activity size={28} color="#3b82f6" /> Mission-Critical IMS
          </h1>
          <p style={{ color: '#94a3b8', marginTop: 4 }}>Real-time Incident Monitoring Dashboard</p>
        </div>
        <div className="stats-container">
          <div className="stat-box">
            <span className="stat-label">Throughput</span>
            <span className="stat-value" style={{ color: '#3b82f6' }}>{metrics.signals_per_sec_avg_5s?.toFixed(2) || '0.00'}</span>
            <span className="stat-label">signals/sec</span>
          </div>
          <div className="stat-box">
            <span className="stat-label">Active</span>
            <span className="stat-value" style={{ color: '#f87171' }}>{incidents.filter(i => i.status !== 'CLOSED').length}</span>
            <span className="stat-label">incidents</span>
          </div>
          <div className="stat-box">
            <span className="stat-label">Resolved</span>
            <span className="stat-value" style={{ color: '#34d399' }}>{incidents.filter(i => i.status === 'CLOSED').length}</span>
            <span className="stat-label">total</span>
          </div>
        </div>
      </header>

      <main className="dashboard">
        {/* Live Feed */}
        <section className="feed">
          <h2 style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: 8 }}>
            <RefreshCw size={18} className="spin" /> Live Feed
          </h2>
          <AnimatePresence>
            {incidents.length === 0 && (
              <div style={{ textAlign: 'center', color: '#64748b', padding: '3rem' }}>
                <AlertCircle size={48} style={{ opacity: 0.2, marginBottom: '1rem' }} />
                <p>No incidents yet. Send signals to see them here.</p>
              </div>
            )}
            {incidents.map((incident) => (
              <motion.div
                key={incident.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.3 }}
                className={`incident-card ${selectedIncident?.id === incident.id ? 'selected' : ''}`}
                onClick={() => setSelectedIncident(incident)}
                style={{ cursor: 'pointer' }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                  <span className={`severity-badge severity-${incident.severity}`}>
                    {incident.severity}
                  </span>
                  <span className="status-badge" style={{ color: statusColor(incident.status) }}>
                    ● {incident.status}
                  </span>
                </div>
                <h3 style={{ margin: '0 0 0.25rem 0', fontSize: '1rem' }}>{incident.title}</h3>
                <p style={{ color: '#94a3b8', fontSize: '0.85rem', margin: 0 }}>{incident.component_id}</p>
                <div style={{ display: 'flex', gap: '1rem', marginTop: '0.75rem', fontSize: '0.8rem', color: '#64748b' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Clock size={13} /> {incident.start_time ? formatDistanceToNow(new Date(incident.start_time)) + ' ago' : 'N/A'}
                  </span>
                  {incident.mttr_seconds && (
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#10b981' }}>
                      <CheckCircle size={13} /> MTTR: {Number(incident.mttr_seconds).toFixed(0)}s
                    </span>
                  )}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </section>

        {/* Incident Detail Sidebar */}
        <aside className="details">
          {selectedIncident ? (
            <div className="incident-card" style={{ position: 'sticky', top: '2rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h2 style={{ fontSize: '1.1rem', margin: 0 }}>Incident Detail</h2>
                <button onClick={() => setSelectedIncident(null)}
                  style={{ background: 'transparent', padding: 4, minWidth: 'auto' }}>
                  <X size={18} />
                </button>
              </div>
              <hr style={{ borderColor: 'rgba(255,255,255,0.05)', margin: '0.75rem 0' }} />

              <div style={{ fontSize: '0.85rem', lineHeight: 1.8 }}>
                <p><strong>ID:</strong> <span style={{ color: '#94a3b8', fontSize: '0.75rem' }}>{selectedIncident.id}</span></p>
                <p><strong>Component:</strong> {selectedIncident.component_id}</p>
                <p><strong>Severity:</strong> <span className={`severity-badge severity-${selectedIncident.severity}`}>{selectedIncident.severity}</span></p>
                <p><strong>Status:</strong> <span style={{ color: statusColor(selectedIncident.status) }}>● {selectedIncident.status}</span></p>
                <p><strong>Description:</strong> {selectedIncident.description}</p>
                {selectedIncident.start_time && <p><strong>Start:</strong> {new Date(selectedIncident.start_time).toLocaleString()}</p>}
                {selectedIncident.end_time && <p><strong>End:</strong> {new Date(selectedIncident.end_time).toLocaleString()}</p>}
                {selectedIncident.mttr_seconds && <p><strong>MTTR:</strong> {Number(selectedIncident.mttr_seconds).toFixed(1)}s</p>}
              </div>

              {/* State Transition Buttons */}
              {selectedIncident.status !== 'CLOSED' && (
                <div style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {getNextStatus(selectedIncident.status) && getNextStatus(selectedIncident.status) !== 'CLOSED' && (
                    <button
                      onClick={() => handleUpdateStatus(selectedIncident.id, getNextStatus(selectedIncident.status))}
                      style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, width: '100%' }}
                    >
                      <ChevronRight size={16} /> Move to {getNextStatus(selectedIncident.status)}
                    </button>
                  )}
                  <button
                    onClick={() => setShowRcaForm(true)}
                    style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
                             background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)' }}
                  >
                    <Shield size={16} /> Submit RCA & Close
                  </button>
                </div>
              )}

              {/* Raw Signals from MongoDB */}
              <div style={{ marginTop: '1.5rem' }}>
                <h3 style={{ fontSize: '0.9rem', marginBottom: '0.5rem' }}>
                  Raw Signals ({rawSignals.length})
                </h3>
                <div style={{ maxHeight: 200, overflowY: 'auto', fontSize: '0.75rem' }}>
                  {rawSignals.length === 0 ? (
                    <p style={{ color: '#64748b' }}>No raw signals found.</p>
                  ) : (
                    rawSignals.map((sig, i) => (
                      <div key={i} style={{
                        background: 'rgba(15,23,42,0.8)', padding: '8px 10px',
                        borderRadius: 8, marginBottom: 6,
                        border: '1px solid rgba(255,255,255,0.05)'
                      }}>
                        <div style={{ color: '#94a3b8' }}>{sig.signal_type} — {sig.timestamp}</div>
                        <pre style={{ margin: '4px 0 0', color: '#64748b', whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
                          {JSON.stringify(sig.payload, null, 2)}
                        </pre>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div style={{ color: '#64748b', textAlign: 'center', padding: '3rem' }}>
              <AlertCircle size={48} style={{ marginBottom: '1rem', opacity: 0.15 }} />
              <p>Select an incident to view details, raw signals, and perform RCA</p>
            </div>
          )}
        </aside>
      </main>

      {/* RCA Modal */}
      <AnimatePresence>
        {showRcaForm && (
          <motion.div
            className="modal-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="modal-content"
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                <h2 style={{ margin: 0 }}>Root Cause Analysis</h2>
                <button onClick={() => setShowRcaForm(false)}
                  style={{ background: 'transparent', padding: 4, minWidth: 'auto' }}>
                  <X size={20} />
                </button>
              </div>

              <form onSubmit={handleSubmitRca}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                  <div className="form-group">
                    <label>Incident Start</label>
                    <input
                      type="datetime-local"
                      value={rcaData.incident_start || (selectedIncident?.start_time ? selectedIncident.start_time.slice(0, 16) : '')}
                      onChange={e => setRcaData({ ...rcaData, incident_start: e.target.value })}
                    />
                  </div>
                  <div className="form-group">
                    <label>Incident End</label>
                    <input
                      type="datetime-local"
                      value={rcaData.incident_end || new Date().toISOString().slice(0, 16)}
                      onChange={e => setRcaData({ ...rcaData, incident_end: e.target.value })}
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label>Root Cause Category</label>
                  <select
                    value={rcaData.root_cause_category}
                    onChange={e => setRcaData({ ...rcaData, root_cause_category: e.target.value })}
                  >
                    <option value="SOFTWARE_BUG">Software Bug</option>
                    <option value="INFRASTRUCTURE">Infrastructure Failure</option>
                    <option value="NETWORK">Network Issue</option>
                    <option value="HUMAN_ERROR">Human Error</option>
                    <option value="CONFIGURATION">Configuration Error</option>
                    <option value="DEPENDENCY_FAILURE">Dependency Failure</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Fix Applied</label>
                  <textarea
                    required rows="3"
                    value={rcaData.fix_applied}
                    onChange={e => setRcaData({ ...rcaData, fix_applied: e.target.value })}
                    placeholder="Describe what was done to resolve this incident..."
                  />
                </div>

                <div className="form-group">
                  <label>Prevention Steps</label>
                  <textarea
                    required rows="3"
                    value={rcaData.prevention_steps}
                    onChange={e => setRcaData({ ...rcaData, prevention_steps: e.target.value })}
                    placeholder="What measures will prevent this from recurring?"
                  />
                </div>

                <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem' }}>
                  <button type="submit" style={{ flex: 1, background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)' }}>
                    Submit RCA & Close Incident
                  </button>
                  <button type="button" onClick={() => setShowRcaForm(false)}
                    style={{ background: 'transparent', border: '1px solid rgba(255,255,255,0.1)' }}>
                    Cancel
                  </button>
                </div>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default App;

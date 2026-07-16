import { useEffect, useMemo, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import EmptyState from '../components/EmptyState';

const initialMessage = {
  id: 1,
  role: 'assistant',
  content: 'Ask a question about your uploaded financial documents and I\u2019ll answer with grounded sources.',
  sources: []
};

const QaPage = () => {
  const navigate = useNavigate();
  const name = localStorage.getItem('finsight_user') || 'Analyst';
  const token = localStorage.getItem('finsight_token');
  const messagesEndRef = useRef(null);

  const [documents, setDocuments] = useState([]);
  const [activeDocumentId, setActiveDocumentId] = useState('');
  const [messages, setMessages] = useState([initialMessage]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const [uploadForm, setUploadForm] = useState({
    file: null,
    company: '',
    year: '',
    quarter: 'Q1'
  });
  const [expandedSources, setExpandedSources] = useState({});
  const [sidebarOpen, setSidebarOpen] = useState(true);

  useEffect(() => {
    if (!token) {
      navigate('/login');
      return;
    }
    fetchDocuments();
  }, [navigate, token]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const fetchDocuments = async () => {
    try {
      const response = await axios.get('http://localhost:8080/api/documents', {
        headers: { Authorization: `Bearer ${token}` }
      });
      const docs = response.data || [];
      setDocuments(docs);
      if (!activeDocumentId && docs.length) {
        setActiveDocumentId(docs[0].documentId);
      }
    } catch (error) {
      console.error('Failed to load documents', error);
    }
  };

  const activeDocument = useMemo(
    () => documents.find((doc) => doc.documentId === activeDocumentId) || null,
    [activeDocumentId, documents]
  );

  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    setUploading(true);
    setUploadError('');

    if (!uploadForm.file) {
      setUploadError('Please select a PDF file.');
      setUploading(false);
      return;
    }

    const formData = new FormData();
    formData.append('file', uploadForm.file);
    formData.append('company', uploadForm.company);
    formData.append('year', uploadForm.year);
    formData.append('quarter', uploadForm.quarter);

    try {
      const uploadResponse = await axios.post('http://localhost:8000/api/upload', formData, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });

      const payload = {
        documentId: uploadResponse.data.document_id,
        filename: uploadResponse.data.filename,
        company: uploadResponse.data.company,
        year: uploadResponse.data.year,
        quarter: uploadResponse.data.quarter,
        chunkCount: uploadResponse.data.chunk_count
      };

      await axios.post('http://localhost:8080/api/documents', payload, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      setShowUploadModal(false);
      setUploadForm({ file: null, company: '', year: '', quarter: 'Q1' });
      await fetchDocuments();
      setActiveDocumentId(payload.documentId);
    } catch (error) {
      setUploadError(error.response?.data?.detail || 'Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!query.trim() || !activeDocumentId || loading) return;

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: query.trim(),
      sources: []
    };

    setMessages((prev) => [...prev, userMessage]);
    setQuery('');
    setLoading(true);

    try {
      const response = await axios.post(
        'http://localhost:8000/api/qa',
        {
          query: userMessage.content,
          document_id: activeDocumentId
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: response.data.answer || 'No answer returned.',
        sources: response.data.sources || []
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const assistantMessage = {
        id: Date.now() + 2,
        role: 'assistant',
        content: 'I could not answer that question right now. Please try again.',
        sources: []
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-[calc(100vh-64px)] overflow-hidden">
      {/* Sidebar */}
      <aside
        className={`flex flex-col border-r border-white/[0.06] bg-surface-950 transition-all duration-300 ${
          sidebarOpen ? 'w-72 min-w-[288px]' : 'w-0 min-w-0 overflow-hidden'
        }`}
      >
        <div className="flex items-center justify-between border-b border-white/[0.06] px-4 py-3.5">
          <div>
            <h2 className="text-sm font-semibold text-white">Documents</h2>
            <p className="text-xs text-slate-500">{documents.length} uploaded</p>
          </div>
          <button
            onClick={() => setShowUploadModal(true)}
            className="flex h-8 items-center gap-1.5 rounded-lg bg-accent-600/15 px-3 text-xs font-medium text-accent-400 transition-colors hover:bg-accent-600/25"
          >
            <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
            </svg>
            Upload
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-3">
          {documents.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-surface-800">
                <svg className="h-5 w-5 text-slate-500" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                </svg>
              </div>
              <p className="text-xs text-slate-500">No documents yet</p>
              <button
                onClick={() => setShowUploadModal(true)}
                className="mt-2 text-xs font-medium text-accent-400 hover:text-accent-300"
              >
                Upload your first PDF
              </button>
            </div>
          ) : (
            <div className="space-y-1.5">
              {documents.map((doc) => (
                <button
                  key={doc.documentId}
                  onClick={() => setActiveDocumentId(doc.documentId)}
                  className={`group w-full rounded-xl border px-3 py-3 text-left transition-all duration-200 ${
                    activeDocumentId === doc.documentId
                      ? 'border-accent-500/30 bg-accent-500/10'
                      : 'border-transparent hover:border-white/[0.06] hover:bg-white/[0.02]'
                  }`}
                >
                  <div className="flex items-start gap-2.5">
                    <div className={`mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg ${
                      activeDocumentId === doc.documentId ? 'bg-accent-500/20 text-accent-400' : 'bg-surface-800 text-slate-500'
                    }`}>
                      <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={1.8} stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                      </svg>
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium text-white">{doc.company || doc.filename}</p>
                      <p className="mt-0.5 text-xs text-slate-500">
                        {doc.quarter} {doc.year} · {doc.chunkCount || 0} chunks
                      </p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </aside>

      {/* Chat area */}
      <main className="flex flex-1 flex-col overflow-hidden">
        {/* Chat header */}
        <div className="flex items-center justify-between border-b border-white/[0.06] px-5 py-3">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 transition-colors hover:bg-white/[0.04] hover:text-white"
              title="Toggle sidebar"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.8} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25H12" />
              </svg>
            </button>
            <div>
              <p className="section-label">Q&A Workspace</p>
              <h2 className="text-sm font-medium text-white">
                {activeDocument
                  ? `${activeDocument.company} · ${activeDocument.quarter} ${activeDocument.year}`
                  : 'Select a document'}
              </h2>
            </div>
          </div>
          <span className="hidden text-xs text-slate-500 sm:block">Welcome, {name}</span>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-5 py-5">
          <div className="mx-auto max-w-3xl space-y-5">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex animate-fade-in ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`flex max-w-[85%] gap-3 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}>
                  {/* Avatar */}
                  <div className={`mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-xs font-semibold ${
                    message.role === 'user'
                      ? 'bg-accent-500/20 text-accent-400'
                      : 'bg-surface-700 text-slate-400'
                  }`}>
                    {message.role === 'user' ? name.charAt(0).toUpperCase() : 'F'}
                  </div>

                  {/* Bubble */}
                  <div className={`rounded-2xl px-4 py-3 ${
                    message.role === 'user'
                      ? 'bg-accent-600 text-white'
                      : 'border border-white/[0.06] bg-surface-900/70 text-slate-200'
                  }`}>
                    <p className="whitespace-pre-wrap text-sm leading-relaxed">{message.content}</p>

                    {/* Sources */}
                    {message.role === 'assistant' && message.sources?.length > 0 && (
                      <div className="mt-3 border-t border-white/[0.06] pt-2.5">
                        <button
                          type="button"
                          onClick={() =>
                            setExpandedSources((prev) => ({
                              ...prev,
                              [message.id]: !prev[message.id]
                            }))
                          }
                          className="flex items-center gap-1.5 text-xs font-medium text-accent-400 transition-colors hover:text-accent-300"
                        >
                          <svg className={`h-3 w-3 transition-transform ${expandedSources[message.id] ? 'rotate-90' : ''}`} fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
                          </svg>
                          {message.sources.length} source{message.sources.length > 1 ? 's' : ''}
                        </button>

                        {expandedSources[message.id] && (
                          <div className="mt-2.5 space-y-2 animate-slide-up">
                            {message.sources.map((source) => (
                              <div
                                key={source.chunk_id}
                                className="rounded-xl border border-white/[0.04] bg-surface-950/60 p-3"
                              >
                                <div className="mb-2 flex flex-wrap items-center gap-1.5">
                                  <span className="inline-flex items-center rounded-md bg-accent-500/10 px-2 py-0.5 text-[10px] font-medium text-accent-400">
                                    {source.chunk_type}
                                  </span>
                                  <span className="inline-flex items-center rounded-md bg-emerald-500/10 px-2 py-0.5 text-[10px] font-medium text-emerald-400">
                                    Score: {Number(source.rerank_score).toFixed(3)}
                                  </span>
                                  <span className="text-[10px] text-slate-500">
                                    {source.company} · {source.quarter} {source.year} · p.{source.page}
                                  </span>
                                </div>
                                <p className="text-xs leading-relaxed text-slate-400">{source.text_preview}</p>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}

            {/* Typing indicator */}
            {loading && (
              <div className="flex animate-fade-in justify-start">
                <div className="flex gap-3">
                  <div className="mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-surface-700 text-xs font-semibold text-slate-400">
                    F
                  </div>
                  <div className="flex items-center gap-1.5 rounded-2xl border border-white/[0.06] bg-surface-900/70 px-4 py-3">
                    <span className="typing-dot" />
                    <span className="typing-dot" />
                    <span className="typing-dot" />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input */}
        <div className="border-t border-white/[0.06] bg-surface-950/50 px-5 py-4">
          <form onSubmit={handleSendMessage} className="mx-auto max-w-3xl">
            <div className="flex items-center gap-3">
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={
                  activeDocument
                    ? 'Ask a question about this document…'
                    : 'Upload and select a document to begin'
                }
                className="input flex-1"
                disabled={!activeDocument || loading}
              />
              <button
                type="submit"
                disabled={!activeDocument || loading || !query.trim()}
                className="btn-primary shrink-0 px-4 py-3"
                title="Send (Enter)"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
                </svg>
              </button>
            </div>
            <p className="mt-2 text-center text-[11px] text-slate-600">
              Press <kbd className="rounded border border-white/[0.06] bg-surface-800 px-1.5 py-0.5 font-mono text-[10px] text-slate-400">Enter</kbd> to send
            </p>
          </form>
        </div>
      </main>

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4 backdrop-blur-sm animate-fade-in">
          <div className="card w-full max-w-lg p-6 animate-slide-up" style={{ borderColor: 'rgba(255,255,255,0.08)' }}>
            <div className="mb-5 flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-white">Upload document</h3>
                <p className="mt-1 text-sm text-slate-400">Ingest a PDF and register it for Q&A.</p>
              </div>
              <button
                onClick={() => setShowUploadModal(false)}
                className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 transition-colors hover:bg-white/[0.04] hover:text-white"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <form onSubmit={handleUploadSubmit} className="space-y-4">
              <div>
                <label className="label">PDF file</label>
                <div className="flex items-center justify-center rounded-xl border-2 border-dashed border-white/[0.08] bg-surface-900/50 px-4 py-6 transition-colors hover:border-white/[0.12]">
                  <div className="text-center">
                    <svg className="mx-auto mb-2 h-8 w-8 text-slate-500" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                    </svg>
                    <input
                      type="file"
                      accept="application/pdf"
                      onChange={(e) => setUploadForm((prev) => ({ ...prev, file: e.target.files[0] }))}
                      className="text-sm text-slate-400 file:mr-3 file:rounded-lg file:border-0 file:bg-accent-600/15 file:px-3 file:py-1.5 file:text-xs file:font-medium file:text-accent-400 file:transition-colors file:cursor-pointer hover:file:bg-accent-600/25"
                    />
                    {uploadForm.file && (
                      <p className="mt-2 text-xs text-emerald-400">{uploadForm.file.name}</p>
                    )}
                  </div>
                </div>
              </div>

              <div>
                <label className="label">Company name</label>
                <input
                  value={uploadForm.company}
                  onChange={(e) => setUploadForm((prev) => ({ ...prev, company: e.target.value }))}
                  className="input"
                  placeholder="ExampleCorp"
                  required
                />
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="label">Year</label>
                  <input
                    type="number"
                    value={uploadForm.year}
                    onChange={(e) => setUploadForm((prev) => ({ ...prev, year: e.target.value }))}
                    className="input"
                    placeholder="2024"
                    required
                  />
                </div>
                <div>
                  <label className="label">Quarter</label>
                  <select
                    value={uploadForm.quarter}
                    onChange={(e) => setUploadForm((prev) => ({ ...prev, quarter: e.target.value }))}
                    className="input"
                  >
                    <option value="Q1">Q1</option>
                    <option value="Q2">Q2</option>
                    <option value="Q3">Q3</option>
                    <option value="Q4">Q4</option>
                    <option value="FY">FY</option>
                  </select>
                </div>
              </div>

              {uploadError && (
                <div className="rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 animate-slide-up">
                  <p className="text-sm text-red-400">{uploadError}</p>
                </div>
              )}

              <div className="flex justify-end gap-3 pt-1">
                <button
                  type="button"
                  onClick={() => setShowUploadModal(false)}
                  className="btn-ghost"
                >
                  Cancel
                </button>
                <button type="submit" disabled={uploading} className="btn-primary">
                  {uploading ? (
                    <span className="flex items-center gap-2">
                      <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A8.001 8.001 0 0112 4.001V0C5.373 0 0 5.373 0 12h4c0-2.29.92-4.37 2.414-5.9z" />
                      </svg>
                      Uploading…
                    </span>
                  ) : 'Upload'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default QaPage;

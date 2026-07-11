import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const initialMessage = {
  id: 1,
  role: 'assistant',
  content: 'Ask a question about your uploaded financial documents and I will answer with grounded sources.',
  sources: []
};

const QaPage = () => {
  const navigate = useNavigate();
  const name = localStorage.getItem('finsight_user') || 'Analyst';
  const token = localStorage.getItem('finsight_token');

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

  useEffect(() => {
    if (!token) {
      navigate('/login');
      return;
    }
    fetchDocuments();
  }, [navigate, token]);

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

  const logout = () => {
    localStorage.removeItem('finsight_token');
    localStorage.removeItem('finsight_user');
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <div className="flex min-h-[calc(100vh-73px)] flex-col lg:flex-row">
        <aside className="w-full border-b border-slate-800 bg-slate-900/70 p-5 lg:w-80 lg:border-b-0 lg:border-r">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-white">Documents</h2>
              <p className="text-sm text-slate-400">Select a document to query</p>
            </div>
            <button
              onClick={() => setShowUploadModal(true)}
              className="rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white transition hover:bg-blue-500"
            >
              Upload Document
            </button>
          </div>

          {documents.length === 0 ? (
            <div className="rounded-xl border border-dashed border-slate-700 bg-slate-950/50 p-4 text-sm text-slate-400">
              No documents uploaded yet.
            </div>
          ) : (
            <div className="space-y-2">
              {documents.map((doc) => (
                <button
                  key={doc.documentId}
                  onClick={() => setActiveDocumentId(doc.documentId)}
                  className={`w-full rounded-xl border p-3 text-left transition ${activeDocumentId === doc.documentId ? 'border-blue-500 bg-blue-600/10' : 'border-slate-800 bg-slate-950/50 hover:border-slate-700'}`}
                >
                  <div className="font-medium text-white">{doc.company || doc.filename}</div>
                  <div className="mt-1 text-sm text-slate-400">
                    {doc.quarter} {doc.year}
                  </div>
                  <div className="mt-1 text-xs text-slate-500">{doc.chunkCount || 0} chunks</div>
                </button>
              ))}
            </div>
          )}
        </aside>

        <main className="flex-1 p-4 sm:p-6 lg:p-8">
          <div className="flex h-full flex-col rounded-2xl border border-slate-800 bg-slate-900/80 shadow-2xl shadow-blue-950/20">
            <div className="border-b border-slate-800 px-5 py-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm uppercase tracking-[0.3em] text-blue-400">Q&A Workspace</p>
                  <h2 className="text-xl font-semibold text-white">{activeDocument ? `${activeDocument.company} • ${activeDocument.quarter} ${activeDocument.year}` : 'Select a document'}</h2>
                </div>
                <div className="text-sm text-slate-400">Welcome back, {name}</div>
              </div>
            </div>

            <div className="flex-1 space-y-4 overflow-y-auto p-5">
              {messages.map((message) => (
                <div key={message.id} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[85%] rounded-2xl px-4 py-3 ${message.role === 'user' ? 'bg-blue-600 text-white' : 'border border-slate-800 bg-slate-950/70 text-slate-200'}`}>
                    <p className="whitespace-pre-wrap text-sm leading-6">{message.content}</p>
                    {message.role === 'assistant' && message.sources?.length > 0 && (
                      <div className="mt-3">
                        <button
                          type="button"
                          onClick={() => setExpandedSources((prev) => ({ ...prev, [message.id]: !prev[message.id] }))}
                          className="text-sm font-medium text-blue-400"
                        >
                          {expandedSources[message.id] ? 'Hide sources' : 'Show sources'}
                        </button>
                        {expandedSources[message.id] && (
                          <div className="mt-2 space-y-2 rounded-xl border border-slate-800 bg-slate-900/70 p-3">
                            {message.sources.map((source) => (
                              <div key={source.chunk_id} className="rounded-lg border border-slate-800 bg-slate-950/70 p-2 text-xs text-slate-400">
                                <div className="flex flex-wrap gap-2 text-slate-300">
                                  <span>Company: {source.company}</span>
                                  <span>•</span>
                                  <span>Quarter: {source.quarter}</span>
                                  <span>•</span>
                                  <span>Year: {source.year}</span>
                                  <span>•</span>
                                  <span>Page: {source.page}</span>
                                </div>
                                <div className="mt-1 flex flex-wrap gap-2 text-slate-400">
                                  <span>Type: {source.chunk_type}</span>
                                  <span>•</span>
                                  <span>Rerank: {Number(source.rerank_score).toFixed(3)}</span>
                                </div>
                                <p className="mt-2 text-slate-300">{source.text_preview}</p>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex justify-start">
                  <div className="rounded-2xl border border-slate-800 bg-slate-950/70 px-4 py-3 text-sm text-slate-300">
                    <div className="flex items-center gap-2">
                      <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A8.001 8.001 0 0112 4.001V0C5.373 0 0 5.373 0 12h4c0-2.29.92-4.37 2.414-5.9z" />
                      </svg>
                      Thinking...
                    </div>
                  </div>
                </div>
              )}
            </div>

            <form onSubmit={handleSendMessage} className="border-t border-slate-800 p-4">
              <div className="flex flex-col gap-3 sm:flex-row">
                <input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder={activeDocument ? 'Ask a question about this document…' : 'Upload and select a document to begin'}
                  className="flex-1 rounded-xl border border-slate-700 bg-slate-950/70 px-4 py-3 text-sm text-white outline-none transition focus:border-blue-500"
                  disabled={!activeDocument || loading}
                />
                <button
                  type="submit"
                  disabled={!activeDocument || loading || !query.trim()}
                  className="rounded-xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  Send
                </button>
              </div>
            </form>
          </div>
        </main>
      </div>

      {showUploadModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 px-4">
          <div className="w-full max-w-lg rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl shadow-blue-950/50">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-white">Upload document</h3>
                <p className="text-sm text-slate-400">Ingest a PDF and register it for Q&A.</p>
              </div>
              <button onClick={() => setShowUploadModal(false)} className="text-sm text-slate-400 hover:text-white">
                Close
              </button>
            </div>

            <form onSubmit={handleUploadSubmit} className="space-y-4">
              <div>
                <label className="mb-1 block text-sm text-slate-300">PDF file</label>
                <input
                  type="file"
                  accept="application/pdf"
                  onChange={(e) => setUploadForm((prev) => ({ ...prev, file: e.target.files[0] }))}
                  className="w-full rounded-xl border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-slate-200"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm text-slate-300">Company name</label>
                <input
                  value={uploadForm.company}
                  onChange={(e) => setUploadForm((prev) => ({ ...prev, company: e.target.value }))}
                  className="w-full rounded-xl border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-white outline-none focus:border-blue-500"
                  placeholder="ExampleCorp"
                  required
                />
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label className="mb-1 block text-sm text-slate-300">Year</label>
                  <input
                    type="number"
                    value={uploadForm.year}
                    onChange={(e) => setUploadForm((prev) => ({ ...prev, year: e.target.value }))}
                    className="w-full rounded-xl border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-white outline-none focus:border-blue-500"
                    placeholder="2024"
                    required
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm text-slate-300">Quarter</label>
                  <select
                    value={uploadForm.quarter}
                    onChange={(e) => setUploadForm((prev) => ({ ...prev, quarter: e.target.value }))}
                    className="w-full rounded-xl border border-slate-700 bg-slate-950/70 px-3 py-2 text-sm text-white outline-none focus:border-blue-500"
                  >
                    <option value="Q1">Q1</option>
                    <option value="Q2">Q2</option>
                    <option value="Q3">Q3</option>
                    <option value="Q4">Q4</option>
                    <option value="FY">FY</option>
                  </select>
                </div>
              </div>

              {uploadError && <p className="text-sm text-red-400">{uploadError}</p>}

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowUploadModal(false)}
                  className="rounded-xl border border-slate-700 px-4 py-2 text-sm text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={uploading}
                  className="rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-70"
                >
                  {uploading ? 'Uploading...' : 'Upload'}
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

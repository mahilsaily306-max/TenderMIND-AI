import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../lib/api';
import toast from 'react-hot-toast';
import type { Tender, Task } from '../types';
import {
  ArrowLeft, Paperclip, MessageSquare, History,
  Plus, CheckCircle2, Circle
} from 'lucide-react';

interface Comment {
  id: number;
  parent_id: number | null;
  author_id: number;
  content: string;
  mentions: string | null;
  created_at: string;
}

interface TimelineEvent {
  id: number;
  action: string;
  user_id: number;
  changes: string | null;
  created_at: string;
}

interface Document {
  id: number;
  original_filename: string;
  file_size_bytes: number;
  mime_type: string;
  status: string;
  created_at: string;
}

export default function TenderDetailPage() {
  const { tenderId } = useParams<{ tenderId: string }>();
  const navigate = useNavigate();
  const [tender, setTender] = useState<Tender | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [comments, setComments] = useState<Comment[]>([]);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [activeTab, setActiveTab] = useState<'tasks' | 'documents' | 'comments' | 'timeline'>('tasks');
  const [loading, setLoading] = useState(true);
  const [newComment, setNewComment] = useState('');
  const [newTaskTitle, setNewTaskTitle] = useState('');

  useEffect(() => {
    if (tenderId) loadTender();
  }, [tenderId]);

  const loadTender = async () => {
    try {
      const [tRes, taskRes, docRes, commentRes, timelineRes] = await Promise.all([
        api.get(`/tenders/${tenderId}`),
        api.get(`/tasks?tender_id=${tenderId}`),
        api.get(`/documents?tender_id=${tenderId}`),
        api.get(`/comments?tender_id=${tenderId}`),
        api.get(`/audit/tender/${tenderId}`),
      ]);
      setTender(tRes.data);
      setTasks(taskRes.data);
      setDocuments(docRes.data);
      setComments(commentRes.data);
      setTimeline(timelineRes.data);
    } catch (err: any) {
      toast.error('Failed to load tender');
      navigate('/dashboard');
    } finally {
      setLoading(false);
    }
  };

  const handleAddComment = async () => {
    if (!newComment.trim()) return;
    try {
      const res = await api.post('/comments', { tender_id: Number(tenderId), content: newComment });
      setComments([...comments, res.data]);
      setNewComment('');
      toast.success('Comment added');
    } catch {
      toast.error('Failed to add comment');
    }
  };

  const handleAddTask = async () => {
    if (!newTaskTitle.trim()) return;
    try {
      const res = await api.post('/tasks', { tender_id: Number(tenderId), title: newTaskTitle });
      setTasks([...tasks, res.data]);
      setNewTaskTitle('');
      toast.success('Task created');
    } catch {
      toast.error('Failed to create task');
    }
  };

  const handleUpdateTaskStatus = async (taskId: number, status: string) => {
    try {
      await api.patch(`/tasks/${taskId}`, { status });
      setTasks(tasks.map(t => t.id === taskId ? { ...t, status: status as any } : t));
      toast.success('Task updated');
    } catch {
      toast.error('Failed to update task');
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('tender_id', String(tenderId));
    formData.append('file', file);
    try {
      const res = await api.post('/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setDocuments([res.data, ...documents]);
      toast.success('Document uploaded');
    } catch {
      toast.error('Upload failed');
    }
  };

  if (loading) return <div className="min-h-screen flex items-center justify-center"><div className="text-gray-500">Loading...</div></div>;
  if (!tender) return null;

  const taskStats = {
    total: tasks.length,
    completed: tasks.filter(t => t.status === 'completed').length,
    pending: tasks.filter(t => t.status === 'pending' || t.status === 'in_progress').length,
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button onClick={() => navigate(-1)} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg">
              <ArrowLeft size={20} />
            </button>
            <div>
              <h1 className="text-xl font-bold">{tender.title}</h1>
              <p className="text-sm text-gray-500">Ref: {tender.reference_number || 'N/A'} | Deadline: {tender.bid_deadline ? new Date(tender.bid_deadline).toLocaleDateString() : 'N/A'}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <StatusBadge status={tender.status} />
            {tender.estimated_value && (
              <span className="text-sm font-medium">${tender.estimated_value.toLocaleString()}</span>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Task stats sidebar */}
          <div className="space-y-4">
            <div className="bg-white dark:bg-gray-900 rounded-xl p-4 border shadow-sm">
              <h3 className="text-sm font-medium text-gray-500 mb-3">Tasks</h3>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm">Total</span>
                  <span className="font-bold">{taskStats.total}</span>
                </div>
                <div className="flex items-center justify-between text-green-600">
                  <span className="text-sm">Done</span>
                  <span className="font-bold">{taskStats.completed}</span>
                </div>
                <div className="flex items-center justify-between text-amber-600">
                  <span className="text-sm">Pending</span>
                  <span className="font-bold">{taskStats.pending}</span>
                </div>
              </div>
            </div>
            <div className="bg-white dark:bg-gray-900 rounded-xl p-4 border shadow-sm">
              <h3 className="text-sm font-medium text-gray-500 mb-3">Documents</h3>
              <p className="text-2xl font-bold">{documents.length}</p>
            </div>
          </div>

          {/* Main content */}
          <div className="lg:col-span-3 space-y-6">
            {/* Tabs */}
            <div className="flex gap-1 bg-gray-100 dark:bg-gray-800 p-1 rounded-lg w-fit">
              {(['tasks', 'documents', 'comments', 'timeline'] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    activeTab === tab
                      ? 'bg-white dark:bg-gray-700 shadow-sm'
                      : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
                  }`}
                >
                  {tab === 'tasks' && <><Circle size={14} className="inline mr-1" />Tasks</>}
                  {tab === 'documents' && <><Paperclip size={14} className="inline mr-1" />Documents</>}
                  {tab === 'comments' && <><MessageSquare size={14} className="inline mr-1" />Comments</>}
                  {tab === 'timeline' && <><History size={14} className="inline mr-1" />Timeline</>}
                </button>
              ))}
            </div>

            {/* Tasks Tab */}
            {activeTab === 'tasks' && (
              <div className="bg-white dark:bg-gray-900 rounded-xl border shadow-sm p-6">
                <div className="flex gap-2 mb-4">
                  <input
                    value={newTaskTitle}
                    onChange={e => setNewTaskTitle(e.target.value)}
                    placeholder="Add a new task..."
                    className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-transparent text-sm"
                  />
                  <button onClick={handleAddTask} className="px-3 py-2 bg-brand-600 text-white rounded-lg text-sm hover:bg-brand-700">
                    <Plus size={16} />
                  </button>
                </div>
                <div className="space-y-2">
                  {tasks.map(task => (
                    <div key={task.id} className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800">
                      <button onClick={() => handleUpdateTaskStatus(task.id, task.status === 'completed' ? 'pending' : 'completed')}>
                        {task.status === 'completed' ? (
                          <CheckCircle2 size={20} className="text-green-500" />
                        ) : (
                          <Circle size={20} className="text-gray-400" />
                        )}
                      </button>
                      <div className="flex-1">
                        <p className={`text-sm ${task.status === 'completed' ? 'line-through text-gray-400' : ''}`}>{task.title}</p>
                        <p className="text-xs text-gray-400">
                          Priority: {task.priority} | {task.assigned_to ? `Assigned to #${task.assigned_to}` : 'Unassigned'}
                        </p>
                      </div>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        task.priority === 'urgent' ? 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300' :
                        task.priority === 'high' ? 'bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300' :
                        'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'
                      }`}>{task.priority}</span>
                    </div>
                  ))}
                  {tasks.length === 0 && <p className="text-sm text-gray-400 text-center py-4">No tasks yet</p>}
                </div>
              </div>
            )}

            {/* Documents Tab */}
            {activeTab === 'documents' && (
              <div className="bg-white dark:bg-gray-900 rounded-xl border shadow-sm p-6">
                <label className="flex items-center gap-2 px-4 py-3 border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-lg cursor-pointer hover:border-brand-500 mb-4">
                  <Paperclip size={18} className="text-gray-400" />
                  <span className="text-sm text-gray-500">Upload document</span>
                  <input type="file" onChange={handleFileUpload} className="hidden" />
                </label>
                <div className="space-y-2">
                  {documents.map(doc => (
                    <div key={doc.id} className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800">
                      <div className="flex items-center gap-3">
                        <Paperclip size={16} className="text-gray-400" />
                        <span className="text-sm">{doc.original_filename}</span>
                        <span className="text-xs text-gray-400">({(doc.file_size_bytes / 1024).toFixed(1)} KB)</span>
                      </div>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        doc.status === 'parsed' ? 'bg-green-100 text-green-700' :
                        doc.status === 'failed' ? 'bg-red-100 text-red-700' :
                        'bg-gray-100 text-gray-600'
                      }`}>{doc.status}</span>
                    </div>
                  ))}
                  {documents.length === 0 && <p className="text-sm text-gray-400 text-center py-4">No documents uploaded</p>}
                </div>
              </div>
            )}

            {/* Comments Tab */}
            {activeTab === 'comments' && (
              <div className="bg-white dark:bg-gray-900 rounded-xl border shadow-sm p-6">
                <div className="space-y-4 mb-4">
                  {comments.map(comment => (
                    <div key={comment.id} className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                      <p className="text-sm whitespace-pre-wrap">{comment.content}</p>
                      <p className="text-xs text-gray-400 mt-1">
                        User #{comment.author_id} · {new Date(comment.created_at).toLocaleString()}
                      </p>
                    </div>
                  ))}
                  {comments.length === 0 && <p className="text-sm text-gray-400 text-center py-4">No comments yet</p>}
                </div>
                <div className="flex gap-2">
                  <textarea
                    value={newComment}
                    onChange={e => setNewComment(e.target.value)}
                    placeholder="Add a comment... (use @name to mention)"
                    rows={2}
                    className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-transparent text-sm resize-none"
                  />
                  <button onClick={handleAddComment} className="px-4 py-2 bg-brand-600 text-white rounded-lg text-sm hover:bg-brand-700 self-end">
                    Send
                  </button>
                </div>
              </div>
            )}

            {/* Timeline Tab */}
            {activeTab === 'timeline' && (
              <div className="bg-white dark:bg-gray-900 rounded-xl border shadow-sm p-6">
                <div className="relative">
                  {timeline.map((event, i) => (
                    <div key={event.id} className="flex gap-4 pb-6 relative">
                      {i < timeline.length - 1 && (
                        <div className="absolute left-[7px] top-4 bottom-0 w-px bg-gray-200 dark:bg-gray-700" />
                      )}
                      <div className="w-4 h-4 rounded-full bg-brand-100 dark:bg-brand-900 border-2 border-brand-500 mt-1 shrink-0" />
                      <div>
                        <p className="text-sm font-medium">{event.action.replace(/\./g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</p>
                        <p className="text-xs text-gray-400">By user #{event.user_id} · {new Date(event.created_at).toLocaleString()}</p>
                        {event.changes && <p className="text-xs text-gray-500 mt-1">{event.changes}</p>}
                      </div>
                    </div>
                  ))}
                  {timeline.length === 0 && <p className="text-sm text-gray-400 text-center py-4">No activity recorded</p>}
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { color: string; label: string }> = {
    identified: { color: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300', label: 'Identified' },
    qualification: { color: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300', label: 'Qualification' },
    in_progress: { color: 'bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300', label: 'In Progress' },
    internal_review: { color: 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300', label: 'Internal Review' },
    submitted: { color: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300', label: 'Submitted' },
    won: { color: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-300', label: 'Won' },
    lost: { color: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300', label: 'Lost' },
    withdrawn: { color: 'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400', label: 'Withdrawn' },
  };
  const c = config[status] || config.identified;
  return (
    <span className={`inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full font-medium ${c.color}`}>
      <span className="w-1.5 h-1.5 rounded-full bg-current" />
      {c.label}
    </span>
  );
}

import React, { useState, useEffect } from 'react';
import { 
  HelpCircle, 
  MessageSquare, 
  Award, 
  Star, 
  Plus, 
  Search, 
  CheckCircle2, 
  ThumbsUp, 
  Briefcase, 
  ArrowRight,
  Sparkles
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';
import { API, getErrorMessage } from '../lib/api';

export const AskAPro = ({ onBookPro }) => {
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [showAskModal, setShowAskModal] = useState(false);
  const [selectedQuestion, setSelectedQuestion] = useState(null);
  const [answers, setAnswers] = useState([]);
  const [answerText, setAnswerText] = useState('');

  const [askForm, setAskForm] = useState({
    title: '',
    description: '',
    category: 'plumbing',
    language: 'English'
  });

  const categories = [
    { id: 'all', label: 'All Trades' },
    { id: 'plumbing', label: 'Plumbing' },
    { id: 'electrical', label: 'Electrical' },
    { id: 'ac_service', label: 'AC & Appliance' },
    { id: 'carpentry', label: 'Carpentry' },
    { id: 'painting', label: 'Painting' }
  ];

  useEffect(() => {
    fetchQuestions();
  }, [selectedCategory, searchQuery]);

  const fetchQuestions = async () => {
    try {
      setLoading(true);
      const params = {};
      if (selectedCategory !== 'all') params.category = selectedCategory;
      if (searchQuery) params.search = searchQuery;

      const res = await axios.get(`${API}/ask-pro/questions`, { params });
      setQuestions(res.data || []);
    } catch (err) {
      console.error(err);
      toast.error('Failed to load Q&A questions');
    } finally {
      setLoading(false);
    }
  };

  const openQuestionDetails = async (q) => {
    setSelectedQuestion(q);
    try {
      const res = await axios.get(`${API}/ask-pro/questions/${q.id}/answers`);
      setAnswers(res.data || []);
    } catch (err) {
      console.error(err);
    }
  };

  const handleCreateQuestion = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/ask-pro/questions`, askForm, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Question published to Ask A Pro community!');
      setShowAskModal(false);
      setAskForm({ title: '', description: '', category: 'plumbing', language: 'English' });
      fetchQuestions();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to publish question'));
    }
  };

  const handlePostAnswer = async (e) => {
    e.preventDefault();
    if (!answerText.trim() || !selectedQuestion) return;
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${API}/ask-pro/questions/${selectedQuestion.id}/answers`,
        { answer_text: answerText },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('Your professional advice was posted!');
      setAnswerText('');
      openQuestionDetails(selectedQuestion);
      fetchQuestions();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Only verified service pros can answer'));
    }
  };

  const handleMarkHelpful = async (answerId) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${API}/ask-pro/answers/${answerId}/mark-helpful`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('⭐ Marked as Most Helpful! +1 Helpful Pro Point awarded to worker.');
      openQuestionDetails(selectedQuestion);
    } catch (err) {
      toast.error(getErrorMessage(err, 'Only question author can mark helpful'));
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-blue-700 via-indigo-700 to-purple-700 p-6 rounded-2xl text-white shadow-xl flex flex-wrap justify-between items-center gap-4">
        <div className="flex items-center space-x-3">
          <div className="p-3 bg-white/20 rounded-xl backdrop-blur-md">
            <HelpCircle className="w-7 h-7 text-white" />
          </div>
          <div>
            <span className="text-xs uppercase font-bold tracking-wider text-blue-200">Community Knowledge</span>
            <h1 className="text-2xl font-bold">Ask A Pro</h1>
            <p className="text-xs text-blue-100 mt-0.5">Ask household service questions & get answered by verified trade professionals</p>
          </div>
        </div>

        <button
          onClick={() => setShowAskModal(true)}
          className="px-4 py-2.5 bg-white text-blue-800 hover:bg-blue-50 rounded-xl font-bold text-sm shadow-sm transition flex items-center"
        >
          <Plus className="w-4 h-4 mr-2" />
          Ask a Question
        </button>
      </div>

      {/* Filter & Search Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
        <div className="flex flex-wrap gap-2">
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition ${
                selectedCategory === cat.id
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>

        <div className="relative w-full sm:w-64">
          <Search className="w-4 h-4 absolute left-3 top-3 text-gray-400" />
          <input
            type="text"
            placeholder="Search Q&A..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-xs border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Question Detail View */}
      {selectedQuestion ? (
        <div className="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm space-y-6">
          <button
            onClick={() => setSelectedQuestion(null)}
            className="text-xs font-bold text-blue-600 hover:underline mb-2 block"
          >
            ← Back to all questions
          </button>

          <div>
            <span className="text-xs font-bold text-blue-600 uppercase tracking-wider">{selectedQuestion.category}</span>
            <h2 className="text-2xl font-bold text-gray-900 mt-1">{selectedQuestion.title}</h2>
            <p className="text-sm text-gray-700 mt-2 bg-gray-50 p-4 rounded-xl border border-gray-100">{selectedQuestion.description}</p>
            <span className="text-xs text-gray-400 mt-2 block">Asked by {selectedQuestion.customer_name}</span>
          </div>

          {/* Answers Section */}
          <div className="space-y-4 pt-4 border-t">
            <h3 className="text-lg font-bold text-gray-900 flex items-center">
              <MessageSquare className="w-5 h-5 mr-2 text-blue-600" />
              Pro Answers ({answers.length})
            </h3>

            {answers.length === 0 ? (
              <p className="text-xs text-gray-500 italic">No answers yet. Verified trade professionals can post an answer below.</p>
            ) : (
              <div className="space-y-4">
                {answers.map((ans) => (
                  <div 
                    key={ans.id} 
                    className={`p-5 rounded-2xl border transition space-y-3 ${
                      ans.is_most_helpful ? 'bg-amber-50/70 border-amber-300 shadow-sm' : 'bg-gray-50 border-gray-200'
                    }`}
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 rounded-full bg-blue-600 text-white font-bold flex items-center justify-center text-sm shadow">
                          {ans.worker_name[0]}
                        </div>
                        <div>
                          <div className="flex items-center space-x-2">
                            <h4 className="font-bold text-gray-900 text-sm">{ans.worker_name}</h4>
                            <span className="text-xs font-semibold px-2 py-0.5 bg-blue-100 text-blue-800 rounded-full">
                              {ans.worker_trade}
                            </span>
                            <span className="text-xs text-amber-600 font-bold flex items-center">
                              <Star className="w-3 h-3 fill-current mr-0.5" />
                              {ans.worker_rating}
                            </span>
                          </div>
                        </div>
                      </div>

                      {ans.is_most_helpful && (
                        <span className="bg-amber-500 text-white px-2.5 py-1 rounded-full text-xs font-bold flex items-center shadow-sm">
                          <Award className="w-3.5 h-3.5 mr-1" />
                          Most Helpful Pro Answer
                        </span>
                      )}
                    </div>

                    <p className="text-sm text-gray-800 leading-relaxed">{ans.answer_text}</p>

                    <div className="flex flex-wrap justify-between items-center pt-2 border-t border-gray-200/60 gap-2">
                      {!ans.is_most_helpful && (
                        <button
                          onClick={() => handleMarkHelpful(ans.id)}
                          className="text-xs font-bold text-amber-700 hover:text-amber-900 flex items-center"
                        >
                          <ThumbsUp className="w-3.5 h-3.5 mr-1" />
                          Mark as Most Helpful
                        </button>
                      )}

                      <button
                        onClick={() => onBookPro && onBookPro(ans.worker_id, ans.worker_name)}
                        className="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-lg transition flex items-center shadow-sm ml-auto"
                      >
                        <Briefcase className="w-3.5 h-3.5 mr-1.5" />
                        Book this Pro
                        <ArrowRight className="w-3 h-3 ml-1" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Post Answer Form */}
            <form onSubmit={handlePostAnswer} className="space-y-3 pt-4 border-t">
              <label className="block text-xs font-bold text-gray-700">Answer as a Verified Service Professional</label>
              <textarea
                required
                rows={3}
                value={answerText}
                onChange={(e) => setAnswerText(e.target.value)}
                placeholder="Provide clear technical advice or solution..."
                className="w-full text-sm border border-gray-300 rounded-xl p-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                type="submit"
                className="px-4 py-2 bg-blue-600 text-white rounded-lg text-xs font-bold hover:bg-blue-700 shadow-sm"
              >
                Post Answer
              </button>
            </form>
          </div>
        </div>
      ) : (
        /* Questions List */
        <div className="space-y-4">
          {loading ? (
            <div className="p-6 bg-white rounded-xl shadow-sm border border-gray-100 animate-pulse"></div>
          ) : questions.length === 0 ? (
            <div className="p-8 text-center bg-gray-50 border border-dashed border-gray-300 rounded-2xl">
              <HelpCircle className="w-10 h-10 text-blue-400 mx-auto mb-2" />
              <p className="text-sm font-semibold text-gray-700">No Questions Found</p>
              <p className="text-xs text-gray-400 mt-1">Be the first to ask a household service question!</p>
            </div>
          ) : (
            questions.map((q) => (
              <div
                key={q.id}
                onClick={() => openQuestionDetails(q)}
                className="bg-white p-5 rounded-2xl border border-gray-200 shadow-sm hover:border-blue-300 hover:shadow-md transition cursor-pointer space-y-2"
              >
                <div className="flex justify-between items-start">
                  <div>
                    <span className="text-xs font-bold text-blue-600 uppercase tracking-wider">{q.category}</span>
                    <h3 className="text-lg font-bold text-gray-900 mt-0.5">{q.title}</h3>
                  </div>
                  <span className="text-xs font-bold px-2.5 py-1 bg-blue-50 text-blue-700 rounded-full flex items-center">
                    <MessageSquare className="w-3.5 h-3.5 mr-1" />
                    {q.answers_count} Answers
                  </span>
                </div>

                <p className="text-xs text-gray-600 line-clamp-2">{q.description}</p>
                <div className="flex justify-between items-center text-xs text-gray-400 pt-2 border-t">
                  <span>Asked by {q.customer_name}</span>
                  <span className="text-blue-600 font-semibold flex items-center">View Answers & Book Pro →</span>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Ask Question Modal */}
      {showAskModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <h3 className="text-lg font-bold text-gray-900">Ask a Service Professional</h3>
            <form onSubmit={handleCreateQuestion} className="space-y-3">
              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Category</label>
                <select
                  value={askForm.category}
                  onChange={(e) => setAskForm({ ...askForm, category: e.target.value })}
                  className="w-full text-sm border border-gray-300 rounded-lg p-2.5 bg-white"
                >
                  <option value="plumbing">Plumbing</option>
                  <option value="electrical">Electrical</option>
                  <option value="ac_service">AC & Appliance</option>
                  <option value="carpentry">Carpentry</option>
                  <option value="painting">Painting</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Question Title</label>
                <input
                  type="text"
                  required
                  value={askForm.title}
                  onChange={(e) => setAskForm({ ...askForm, title: e.target.value })}
                  placeholder="e.g. My AC makes a rattling noise"
                  className="w-full text-sm border border-gray-300 rounded-lg p-2.5 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Detailed Description</label>
                <textarea
                  required
                  rows={3}
                  value={askForm.description}
                  onChange={(e) => setAskForm({ ...askForm, description: e.target.value })}
                  placeholder="Describe what's wrong or what advice you need..."
                  className="w-full text-sm border border-gray-300 rounded-lg p-2.5 focus:outline-none"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAskModal(false)}
                  className="px-4 py-2 text-sm font-semibold text-gray-600 hover:bg-gray-100 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-sm font-bold text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm"
                >
                  Publish Question
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  CheckCircle2, 
  Clock, 
  AlertCircle, 
  ShieldCheck, 
  DollarSign, 
  Calendar, 
  UserCheck, 
  Plus, 
  Check, 
  X, 
  History,
  FileDiff
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';
import { API, getErrorMessage } from '../lib/api';

export const ScopeAgreementCard = ({ jobId, userRole, currentUserId }) => {
  const [agreement, setAgreement] = useState(null);
  const [changeRequests, setChangeRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showChangeModal, setShowChangeModal] = useState(false);
  const [changeDesc, setChangeDesc] = useState('');
  const [priceDelta, setPriceDelta] = useState(0);
  const [submittingChange, setSubmittingChange] = useState(false);

  useEffect(() => {
    if (jobId) {
      fetchAgreement();
    }
  }, [jobId]);

  const fetchAgreement = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      const res = await axios.get(`${API}/agreements/job/${jobId}`, { headers });
      setAgreement(res.data);

      if (res.data?.id) {
        const crRes = await axios.get(`${API}/agreements/${res.data.id}/change-requests`, { headers });
        setChangeRequests(crRes.data || []);
      }
    } catch (err) {
      console.error(err);
      toast.error(getErrorMessage(err, 'Failed to load Scope Agreement'));
    } finally {
      setLoading(false);
    }
  };

  const handleAgree = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await axios.post(
        `${API}/agreements/${agreement.id}/agree`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setAgreement(res.data);
      toast.success('You have agreed to the Scope Agreement!');
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to sign agreement'));
    }
  };

  const handleCreateChangeRequest = async (e) => {
    e.preventDefault();
    if (!changeDesc.trim()) return;

    try {
      setSubmittingChange(true);
      const token = localStorage.getItem('token');
      const newPrice = (agreement?.agreed_price || 0) + parseFloat(priceDelta || 0);

      await axios.post(
        `${API}/agreements/${agreement.id}/change-requests`,
        {
          description: changeDesc,
          price_change: parseFloat(priceDelta || 0),
          new_agreed_price: newPrice,
          additional_notes: 'Scope adjustment requested'
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      toast.success('Change request submitted for review!');
      setShowChangeModal(false);
      setChangeDesc('');
      setPriceDelta(0);
      fetchAgreement();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to submit change request'));
    } finally {
      setSubmittingChange(false);
    }
  };

  const handleRespondChangeRequest = async (requestId, status) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${API}/agreements/change-requests/${requestId}/respond`,
        { status, response_notes: `Marked as ${status}` },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success(`Change request ${status}!`);
      fetchAgreement();
    } catch (err) {
      toast.error(getErrorMessage(err, `Failed to ${status} change request`));
    }
  };

  if (loading) {
    return (
      <div className="p-6 bg-white rounded-xl shadow-sm border border-gray-100 animate-pulse space-y-4">
        <div className="h-6 bg-gray-200 rounded w-1/3"></div>
        <div className="h-20 bg-gray-100 rounded"></div>
      </div>
    );
  }

  if (!agreement) return null;

  const isCustomer = userRole === 'customer' || currentUserId === agreement.customer_id;
  const isWorker = userRole === 'worker' || currentUserId === agreement.worker_id;

  const hasCustomerAgreed = !!agreement.customer_agreed_at;
  const hasWorkerAgreed = !!agreement.worker_agreed_at;
  const userHasAgreed = isCustomer ? hasCustomerAgreed : isWorker ? hasWorkerAgreed : false;

  return (
    <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden mb-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-orange-600 to-amber-600 p-5 text-white flex flex-wrap justify-between items-center gap-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-white/20 rounded-lg backdrop-blur-sm">
            <FileText className="w-6 h-6 text-white" />
          </div>
          <div>
            <span className="text-xs uppercase font-bold tracking-wider text-orange-100">Digital Contract</span>
            <h2 className="text-xl font-bold">{agreement.job_title}</h2>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <span className={`px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider ${
            agreement.status === 'active' 
              ? 'bg-emerald-500 text-white' 
              : 'bg-amber-400 text-gray-900'
          }`}>
            {agreement.status === 'active' ? '✓ ACTIVE AGREEMENT' : '⏳ DRAFT AGREEMENT'}
          </span>
        </div>
      </div>

      {/* Contract Details */}
      <div className="p-6 space-y-6">
        {/* Included vs Excluded Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-emerald-50/60 border border-emerald-100 p-4 rounded-xl">
            <h4 className="text-sm font-bold text-emerald-900 flex items-center mb-3">
              <CheckCircle2 className="w-4 h-4 mr-2 text-emerald-600" />
              Work Included in Scope
            </h4>
            <ul className="space-y-2 text-sm text-gray-700">
              {agreement.work_included?.map((item, idx) => (
                <li key={idx} className="flex items-start">
                  <span className="text-emerald-500 mr-2">•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="bg-rose-50/60 border border-rose-100 p-4 rounded-xl">
            <h4 className="text-sm font-bold text-rose-900 flex items-center mb-3">
              <AlertCircle className="w-4 h-4 mr-2 text-rose-600" />
              Work NOT Included
            </h4>
            <ul className="space-y-2 text-sm text-gray-700">
              {agreement.work_not_included?.map((item, idx) => (
                <li key={idx} className="flex items-start">
                  <span className="text-rose-500 mr-2">•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Pricing, Schedule & Responsibilities Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 bg-gray-50 p-4 rounded-xl border border-gray-100 text-sm">
          <div>
            <span className="text-xs text-gray-500 block font-medium">Agreed Price</span>
            <span className="text-lg font-bold text-gray-900 text-orange-600">₹{agreement.agreed_price?.toLocaleString()}</span>
          </div>

          <div>
            <span className="text-xs text-gray-500 block font-medium">Materials</span>
            <span className="font-semibold text-gray-800">{agreement.materials_responsibility}</span>
          </div>

          <div>
            <span className="text-xs text-gray-500 block font-medium">Start Date & Time</span>
            <span className="font-semibold text-gray-800">{agreement.start_date} @ {agreement.start_time}</span>
          </div>

          <div>
            <span className="text-xs text-gray-500 block font-medium">Warranty</span>
            <span className="font-semibold text-emerald-700 flex items-center">
              <ShieldCheck className="w-4 h-4 mr-1 text-emerald-600" />
              {agreement.warranty}
            </span>
          </div>
        </div>

        {/* Agreement Status Badges & Action Buttons */}
        <div className="border-t pt-4 flex flex-wrap justify-between items-center gap-4">
          <div className="flex items-center space-x-6 text-sm">
            <div className="flex items-center space-x-2">
              <span className="text-gray-600 font-medium">Customer:</span>
              {hasCustomerAgreed ? (
                <span className="text-xs font-semibold px-2 py-0.5 bg-emerald-100 text-emerald-800 rounded flex items-center">
                  <Check className="w-3 h-3 mr-1" /> Agreed
                </span>
              ) : (
                <span className="text-xs font-semibold px-2 py-0.5 bg-amber-100 text-amber-800 rounded">Pending</span>
              )}
            </div>

            <div className="flex items-center space-x-2">
              <span className="text-gray-600 font-medium">Worker:</span>
              {hasWorkerAgreed ? (
                <span className="text-xs font-semibold px-2 py-0.5 bg-emerald-100 text-emerald-800 rounded flex items-center">
                  <Check className="w-3 h-3 mr-1" /> Agreed
                </span>
              ) : (
                <span className="text-xs font-semibold px-2 py-0.5 bg-amber-100 text-amber-800 rounded">Pending</span>
              )}
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={() => setShowChangeModal(true)}
              className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-semibold text-gray-700 hover:bg-gray-50 flex items-center"
            >
              <FileDiff className="w-4 h-4 mr-2 text-gray-500" />
              Propose Change
            </button>

            {!userHasAgreed && agreement.status !== 'active' && (
              <button
                onClick={handleAgree}
                className="px-5 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg text-sm font-bold transition shadow-sm flex items-center"
              >
                <Check className="w-4 h-4 mr-2" />
                Agree to Scope
              </button>
            )}
          </div>
        </div>

        {/* Change Requests Section */}
        {changeRequests.length > 0 && (
          <div className="border-t pt-4 space-y-3">
            <h4 className="text-sm font-bold text-gray-800 flex items-center">
              <FileDiff className="w-4 h-4 mr-2 text-orange-600" />
              Change Requests ({changeRequests.length})
            </h4>
            <div className="space-y-2">
              {changeRequests.map((cr) => (
                <div key={cr.id} className="p-3 bg-gray-50 rounded-xl border border-gray-200 flex flex-wrap justify-between items-center gap-3 text-sm">
                  <div>
                    <span className="font-semibold text-gray-900">{cr.description}</span>
                    <span className="text-xs text-gray-500 ml-2">
                      (Price adjustment: {cr.price_change >= 0 ? `+₹${cr.price_change}` : `-₹${Math.abs(cr.price_change)}`})
                    </span>
                  </div>

                  <div className="flex items-center space-x-2">
                    <span className={`text-xs font-bold uppercase px-2 py-0.5 rounded ${
                      cr.status === 'approved' ? 'bg-emerald-100 text-emerald-800' :
                      cr.status === 'declined' ? 'bg-rose-100 text-rose-800' : 'bg-amber-100 text-amber-800'
                    }`}>
                      {cr.status}
                    </span>

                    {cr.status === 'pending' && cr.requester_id !== currentUserId && (
                      <div className="flex items-center space-x-1">
                        <button
                          onClick={() => handleRespondChangeRequest(cr.id, 'approved')}
                          className="px-2.5 py-1 bg-emerald-600 text-white rounded text-xs font-bold hover:bg-emerald-700"
                        >
                          Approve
                        </button>
                        <button
                          onClick={() => handleRespondChangeRequest(cr.id, 'declined')}
                          className="px-2.5 py-1 bg-rose-600 text-white rounded text-xs font-bold hover:bg-rose-700"
                        >
                          Decline
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Audit Trail History Log */}
        {agreement.history?.length > 0 && (
          <div className="border-t pt-4">
            <details className="text-xs text-gray-500">
              <summary className="font-semibold cursor-pointer text-gray-700 hover:text-gray-900 flex items-center">
                <History className="w-3.5 h-3.5 mr-1" />
                Agreement History ({agreement.history.length} events)
              </summary>
              <div className="mt-2 space-y-1 pl-4 border-l-2 border-gray-200">
                {agreement.history.map((h, i) => (
                  <div key={i} className="py-1">
                    <span className="font-medium text-gray-700">{h.summary}</span>
                    <span className="text-gray-400 ml-2">({new Date(h.timestamp).toLocaleTimeString()})</span>
                  </div>
                ))}
              </div>
            </details>
          </div>
        )}
      </div>

      {/* Propose Change Modal */}
      {showChangeModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 max-w-md w-full shadow-2xl">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Propose Scope Change</h3>
            <form onSubmit={handleCreateChangeRequest} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Description of Additional Work</label>
                <textarea
                  required
                  rows={3}
                  value={changeDesc}
                  onChange={(e) => setChangeDesc(e.target.value)}
                  placeholder="e.g. Include balcony painting as requested by customer"
                  className="w-full text-sm border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-orange-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Price Adjustment (₹)</label>
                <input
                  type="number"
                  value={priceDelta}
                  onChange={(e) => setPriceDelta(e.target.value)}
                  placeholder="e.g. +500 or -200"
                  className="w-full text-sm border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-orange-500 focus:outline-none"
                />
                <span className="text-xs text-gray-500 mt-1 block">
                  New total price will be: ₹{(agreement.agreed_price + parseFloat(priceDelta || 0)).toLocaleString()}
                </span>
              </div>

              <div className="flex justify-end space-x-3 pt-3">
                <button
                  type="button"
                  onClick={() => setShowChangeModal(false)}
                  className="px-4 py-2 text-sm font-semibold text-gray-600 hover:bg-gray-100 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingChange}
                  className="px-4 py-2 text-sm font-bold text-white bg-orange-600 hover:bg-orange-700 rounded-lg shadow-sm"
                >
                  Submit Request
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

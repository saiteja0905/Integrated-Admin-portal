import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, 
  Search, 
  Filter, 
  FileText, 
  Camera, 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  Eye, 
  Download, 
  Lock, 
  User, 
  Phone, 
  Clock, 
  Loader2,
  Check
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';
import { API, getErrorMessage } from '../lib/api';

export const AdminWorkerVerification = () => {
  const [verifications, setVerifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  // Selected item for Review Modal
  const [selectedVerif, setSelectedVerif] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  // Action Modals
  const [showConfirmVerify, setShowConfirmVerify] = useState(false);
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [rejectionReason, setRejectionReason] = useState('');
  const [processingAction, setProcessingAction] = useState(false);

  // PDF Secure Viewer Modal
  const [showPdfViewer, setShowPdfViewer] = useState(false);
  const [pdfBlobUrl, setPdfBlobUrl] = useState(null);
  const [loadingPdf, setLoadingPdf] = useState(false);

  useEffect(() => {
    fetchVerifications();
  }, [statusFilter]);

  const fetchVerifications = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const res = await axios.get(`${API}/admin/worker-verifications`, {
        params: { status: statusFilter, search: searchTerm },
        headers: { Authorization: `Bearer ${token}` }
      });
      setVerifications(res.data || []);
    } catch (err) {
      console.error(err);
      toast.error(getErrorMessage(err, 'Failed to fetch worker verifications'));
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchVerifications();
  };

  const openReviewModal = async (verifId) => {
    try {
      setLoadingDetail(true);
      const token = localStorage.getItem('token');
      const res = await axios.get(`${API}/admin/worker-verifications/${verifId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSelectedVerif(res.data);
    } catch (err) {
      toast.error('Could not load verification details');
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleViewPdf = async () => {
    if (!selectedVerif?.id) return;
    try {
      setLoadingPdf(true);
      const token = localStorage.getItem('token');
      const res = await axios.get(
        `${API}/admin/worker-verifications/${selectedVerif.id}/document/labour_certificate`,
        {
          headers: { Authorization: `Bearer ${token}` },
          responseType: 'blob'
        }
      );
      const blob = new Blob([res.data], { type: 'application/pdf' });
      const blobUrl = URL.createObjectURL(blob);
      setPdfBlobUrl(blobUrl);
      setShowPdfViewer(true);
    } catch (err) {
      toast.error('Failed to load certificate PDF document');
    } finally {
      setLoadingPdf(false);
    }
  };

  const handleApproveWorker = async () => {
    if (!selectedVerif?.id) return;
    try {
      setProcessingAction(true);
      const token = localStorage.getItem('token');
      await axios.post(
        `${API}/admin/worker-verifications/${selectedVerif.id}/verify`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('✓ Worker verified successfully!');
      setShowConfirmVerify(false);
      setSelectedVerif(null);
      fetchVerifications();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to verify worker'));
    } finally {
      setProcessingAction(false);
    }
  };

  const handleRejectWorker = async () => {
    if (!selectedVerif?.id || !rejectionReason.trim()) return;
    try {
      setProcessingAction(true);
      const token = localStorage.getItem('token');
      await axios.post(
        `${API}/admin/worker-verifications/${selectedVerif.id}/reject`,
        { rejection_reason: rejectionReason.trim() },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('Worker verification rejected with reason');
      setShowRejectModal(false);
      setRejectionReason('');
      setSelectedVerif(null);
      fetchVerifications();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to reject verification'));
    } finally {
      setProcessingAction(false);
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center">
            <ShieldCheck className="w-7 h-7 text-orange-600 mr-2" />
            Worker Identity Verification
          </h1>
          <p className="text-sm text-gray-600">Review Aadhaar, Labour Certificate PDF, and Live Photographs submitted by workers.</p>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-xs font-bold text-amber-800 bg-amber-100 px-3 py-1.5 rounded-full border border-amber-200">
            {verifications.filter(v => v.status === 'PENDING_VERIFICATION').length} Pending Reviews
          </span>
        </div>
      </div>

      {/* Controls Bar: Search & Status Filter */}
      <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm flex flex-col md:flex-row justify-between gap-4">
        <form onSubmit={handleSearchSubmit} className="flex flex-1 max-w-md gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-gray-400 absolute left-3 top-3" />
            <input
              type="text"
              placeholder="Search by worker name, phone, or trade..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full text-sm pl-9 pr-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
            />
          </div>
          <button type="submit" className="px-4 py-2 bg-orange-600 text-white rounded-lg text-sm font-bold hover:bg-orange-700">
            Search
          </button>
        </form>

        <div className="flex items-center space-x-2">
          <Filter className="w-4 h-4 text-gray-500" />
          <span className="text-xs font-bold text-gray-700">Filter:</span>
          {['all', 'pending_verification', 'verified', 'rejected'].map((f) => (
            <button
              key={f}
              onClick={() => setStatusFilter(f)}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold capitalize transition ${
                statusFilter === f ? 'bg-orange-600 text-white shadow-sm' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {f.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* Worker Verifications Table */}
      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-8 text-center flex justify-center">
            <Loader2 className="w-8 h-8 text-orange-500 animate-spin" />
          </div>
        ) : verifications.length === 0 ? (
          <div className="p-12 text-center text-gray-500 space-y-3">
            <ShieldCheck className="w-12 h-12 text-gray-300 mx-auto" />
            <p className="font-semibold">No Worker Verifications Found</p>
            <p className="text-xs text-gray-400">There are currently no worker identity verification submissions matching your filter.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-gray-50 text-xs font-bold text-gray-500 uppercase border-b border-gray-200">
                  <th className="py-3.5 px-4">Worker</th>
                  <th className="py-3.5 px-4">Trade / Skills</th>
                  <th className="py-3.5 px-4">Documents</th>
                  <th className="py-3.5 px-4">Submitted Date</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 text-sm">
                {verifications.map((v) => (
                  <tr key={v.id} className="hover:bg-gray-50/80 transition">
                    <td className="py-3.5 px-4">
                      <div>
                        <p className="font-bold text-gray-900">{v.worker_name}</p>
                        <p className="text-xs text-gray-500">{v.worker_phone}</p>
                      </div>
                    </td>

                    <td className="py-3.5 px-4">
                      <span className="inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold bg-gray-100 text-gray-800 border">
                        {v.worker_trade || 'General Worker'}
                      </span>
                    </td>

                    <td className="py-3.5 px-4">
                      <div className="flex items-center space-x-2 text-xs text-gray-600 font-semibold">
                        <span className="text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">Aadhaar</span>
                        <span className="text-rose-700 bg-rose-50 px-2 py-0.5 rounded border border-rose-200">Labour PDF</span>
                        <span className="text-purple-700 bg-purple-50 px-2 py-0.5 rounded border border-purple-200">Photo</span>
                      </div>
                    </td>

                    <td className="py-3.5 px-4 text-xs text-gray-500">
                      {v.submitted_at ? new Date(v.submitted_at).toLocaleDateString() : 'N/A'}
                    </td>

                    <td className="py-3.5 px-4">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-extrabold uppercase ${
                        v.status === 'VERIFIED' ? 'bg-emerald-100 text-emerald-800' :
                        v.status === 'REJECTED' ? 'bg-red-100 text-red-800' :
                        'bg-amber-100 text-amber-900 border border-amber-300'
                      }`}>
                        {v.status === 'VERIFIED' && <CheckCircle className="w-3 h-3 mr-1 text-emerald-600" />}
                        {v.status === 'REJECTED' && <XCircle className="w-3 h-3 mr-1 text-red-600" />}
                        {v.status === 'PENDING_VERIFICATION' && <Clock className="w-3 h-3 mr-1 text-amber-600 animate-pulse" />}
                        {v.status.replace('_', ' ')}
                      </span>
                    </td>

                    <td className="py-3.5 px-4 text-right">
                      <button
                        onClick={() => openReviewModal(v.id)}
                        className="px-3 py-1.5 bg-orange-600 text-white rounded-lg text-xs font-bold hover:bg-orange-700 shadow-sm transition inline-flex items-center"
                      >
                        <Eye className="w-3.5 h-3.5 mr-1" />
                        Review
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ADMIN REVIEW MODAL */}
      {selectedVerif && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 max-w-2xl w-full shadow-2xl space-y-6 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-start border-b pb-3">
              <div>
                <span className="text-xs uppercase font-extrabold text-orange-600">Verification Review</span>
                <h2 className="text-xl font-bold text-gray-900">{selectedVerif.worker_name}</h2>
                <p className="text-xs text-gray-500">Phone: {selectedVerif.worker_phone} • Trade: {selectedVerif.worker_trade}</p>
              </div>
              <button
                onClick={() => setSelectedVerif(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <XCircle className="w-6 h-6" />
              </button>
            </div>

            {/* Verification Content Grid */}
            <div className="space-y-4">
              {/* 1. Aadhaar Card */}
              <div className="p-4 bg-gray-50 rounded-xl border border-gray-200 flex justify-between items-center">
                <div>
                  <label className="text-xs font-bold text-gray-500 uppercase">Aadhaar Card Number</label>
                  <p className="text-lg font-bold font-mono text-gray-900 flex items-center mt-0.5">
                    <Lock className="w-4 h-4 text-emerald-600 mr-2" />
                    {selectedVerif.aadhaar_masked}
                  </p>
                </div>
                <span className="text-xs font-bold text-emerald-800 bg-emerald-100 px-3 py-1 rounded-full">
                  ✓ Masked Display
                </span>
              </div>

              {/* 2. Labour Certificate PDF */}
              <div className="p-4 bg-blue-50/50 rounded-xl border border-blue-200 flex justify-between items-center">
                <div className="flex items-center space-x-3">
                  <FileText className="w-8 h-8 text-rose-600" />
                  <div>
                    <label className="text-xs font-bold text-gray-500 uppercase">Labour Certificate PDF</label>
                    <p className="text-sm font-bold text-gray-900">{selectedVerif.labour_certificate_name}</p>
                  </div>
                </div>
                <button
                  onClick={handleViewPdf}
                  disabled={loadingPdf}
                  className="px-4 py-2 bg-rose-600 text-white rounded-lg text-xs font-bold hover:bg-rose-700 shadow-sm flex items-center"
                >
                  {loadingPdf ? <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" /> : <Eye className="w-3.5 h-3.5 mr-1" />}
                  View Certificate
                </button>
              </div>

              {/* 3. Live Photograph */}
              <div className="p-4 bg-purple-50/50 rounded-xl border border-purple-200 space-y-3">
                <label className="text-xs font-bold text-gray-500 uppercase">Live Photograph</label>
                <div className="flex justify-center">
                  <img
                    src={`${API}${selectedVerif.live_photo_url}?token=${localStorage.getItem('token')}`}
                    alt="Live Photograph preview"
                    className="max-h-64 rounded-xl border border-gray-300 shadow-sm object-cover"
                    onError={(e) => {
                      e.target.src = 'https://via.placeholder.com/300x300?text=Live+Photo+Preview';
                    }}
                  />
                </div>
              </div>

              {/* Current Status Badge */}
              <div className="p-3 bg-gray-50 rounded-xl border flex justify-between items-center text-xs">
                <span className="text-gray-500 font-bold">Current Verification Status:</span>
                <span className="font-extrabold text-orange-600 uppercase">{selectedVerif.status}</span>
              </div>
            </div>

            {/* Action Buttons: Approve / Reject */}
            <div className="flex gap-3 pt-3 border-t">
              <button
                onClick={() => setShowRejectModal(true)}
                className="flex-1 px-4 py-3 bg-red-600 text-white rounded-xl font-bold hover:bg-red-700 shadow-sm transition flex items-center justify-center"
              >
                <XCircle className="w-4 h-4 mr-2" />
                Reject
              </button>

              <button
                onClick={() => setShowConfirmVerify(true)}
                className="flex-1 px-4 py-3 bg-emerald-600 text-white rounded-xl font-bold hover:bg-emerald-700 shadow-md transition flex items-center justify-center"
              >
                <CheckCircle className="w-5 h-5 mr-2" />
                Verify Worker
              </button>
            </div>
          </div>
        </div>
      )}

      {/* CONFIRM VERIFY MODAL */}
      {showConfirmVerify && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-4 text-center">
            <div className="w-12 h-12 bg-emerald-100 rounded-full flex items-center justify-center mx-auto text-emerald-600">
              <CheckCircle className="w-7 h-7" />
            </div>
            <h3 className="text-lg font-bold text-gray-900">Verify {selectedVerif?.worker_name}?</h3>
            <p className="text-sm text-gray-600">Are you sure you want to approve and mark this worker as identity verified on Sanyuth?</p>
            
            <div className="flex gap-3 pt-2">
              <button
                onClick={() => setShowConfirmVerify(false)}
                className="flex-1 px-4 py-2.5 border border-gray-300 text-gray-700 rounded-xl font-bold hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleApproveWorker}
                disabled={processingAction}
                className="flex-1 px-4 py-2.5 bg-emerald-600 text-white rounded-xl font-bold hover:bg-emerald-700 shadow flex items-center justify-center disabled:opacity-50"
              >
                {processingAction ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : null}
                Confirm Verification
              </button>
            </div>
          </div>
        </div>
      )}

      {/* REJECT MODAL */}
      {showRejectModal && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <div className="flex justify-between items-center border-b pb-2">
              <h3 className="text-lg font-bold text-gray-900">Reject Worker Verification</h3>
              <button onClick={() => setShowRejectModal(false)} className="text-gray-400 hover:text-gray-600">
                <XCircle className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-gray-600">Provide a clear rejection reason explaining what documents need to be replaced or corrected.</p>

            <div>
              <label className="block text-xs font-bold text-gray-700 mb-1">Rejection Reason *</label>
              <textarea
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                placeholder="e.g. Labour certificate is unclear. Please re-upload a clear PDF document."
                rows={4}
                className="w-full p-3 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-red-500 focus:outline-none"
              />
            </div>

            <div className="flex gap-3 pt-2">
              <button
                onClick={() => setShowRejectModal(false)}
                className="flex-1 px-4 py-2.5 border border-gray-300 text-gray-700 rounded-xl text-xs font-bold hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleRejectWorker}
                disabled={processingAction || !rejectionReason.trim()}
                className="flex-1 px-4 py-2.5 bg-red-600 text-white rounded-xl text-xs font-bold hover:bg-red-700 shadow disabled:opacity-50"
              >
                {processingAction ? 'Rejecting...' : 'Reject & Request Resubmission'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* PDF VIEWER MODAL */}
      {showPdfViewer && (
        <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-4 max-w-4xl w-full h-[85vh] shadow-2xl flex flex-col">
            <div className="flex justify-between items-center border-b pb-3 mb-3">
              <h3 className="font-bold text-gray-900 flex items-center">
                <FileText className="w-5 h-5 text-rose-600 mr-2" />
                Labour Certificate PDF Viewer
              </h3>
              <button onClick={() => setShowPdfViewer(false)} className="text-gray-500 hover:text-gray-700">
                <XCircle className="w-6 h-6" />
              </button>
            </div>
            <div className="flex-1 bg-gray-100 rounded-xl overflow-hidden">
              {pdfBlobUrl ? (
                <iframe src={pdfBlobUrl} title="Labour Certificate PDF" className="w-full h-full border-0" />
              ) : (
                <div className="p-8 text-center">Loading PDF...</div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

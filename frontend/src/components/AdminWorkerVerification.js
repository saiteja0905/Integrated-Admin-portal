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
  Check,
  Calendar,
  MapPin,
  AlertCircle,
  RefreshCw,
  History,
  Shield,
  UserCheck,
  Edit,
  Save
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';
import { API, getErrorMessage } from '../lib/api';

export const AdminWorkerVerification = () => {
  const [verifications, setVerifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  // Selected item for modals
  const [selectedVerif, setSelectedVerif] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  // Modals state
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [showManageModal, setShowManageModal] = useState(false);
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [showConfirmApproveDocs, setShowConfirmApproveDocs] = useState(false);
  const [showRecordOutcomeModal, setShowRecordOutcomeModal] = useState(false);
  const [showCancelModal, setShowCancelModal] = useState(false);

  // Form states
  const [rejectionReason, setRejectionReason] = useState('');
  const [cancellationReason, setCancellationReason] = useState('');
  const [outcomeData, setOutcomeData] = useState({ outcome: 'PASSED', outcome_reason: '', admin_notes: '' });
  const [processingAction, setProcessingAction] = useState(false);

  // Scheduling Form State
  const todayStr = new Date().toISOString().split('T')[0];
  const [scheduleForm, setScheduleForm] = useState({
    location_name: 'Sanyuth Central Verification Hub',
    venue_address: 'Building 5, Innovation Valley, Madhapur, Hyderabad - 500081',
    appointment_date: todayStr,
    start_time: '10:00',
    end_time: '11:00',
    officer_name: 'Ramesh Verma - Senior Verification Officer',
    officer_phone: '+91 98765 43210',
    instructions: 'Please bring your original physical Aadhaar card, original Labour Certificate, and valid government photo ID.',
    admin_notes: '',
    reschedule_reason: ''
  });

  // Manage Modal active tab: 'details', 'edit', 'reschedule', 'outcome', 'history'
  const [manageTab, setManageTab] = useState('details');

  // PDF Viewer Modal
  const [showPdfViewer, setShowPdfViewer] = useState(false);
  const [pdfBlobUrl, setPdfBlobUrl] = useState(null);
  const [loadingPdf, setLoadingPdf] = useState(false);

  // Live Photo state for authenticated loading
  const [livePhotoBlobUrl, setLivePhotoBlobUrl] = useState(null);
  const [loadingPhoto, setLoadingPhoto] = useState(false);

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

  const fetchVerificationDetail = async (verifId) => {
    try {
      setLoadingDetail(true);
      const token = localStorage.getItem('token');
      const res = await axios.get(`${API}/admin/worker-verifications/${verifId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSelectedVerif(res.data);
      return res.data;
    } catch (err) {
      toast.error('Could not load verification details');
      return null;
    } finally {
      setLoadingDetail(false);
    }
  };

  const openReviewModal = async (verifId) => {
    setLivePhotoBlobUrl(null);
    const detail = await fetchVerificationDetail(verifId);
    if (detail) {
      setShowReviewModal(true);
      if (detail.live_photo_url) {
        try {
          setLoadingPhoto(true);
          const token = localStorage.getItem('token');
          const photoRes = await axios.get(
            `${API}/admin/worker-verifications/${verifId}/document/live_photo`,
            {
              headers: { Authorization: `Bearer ${token}` },
              responseType: 'blob'
            }
          );
          const blobUrl = URL.createObjectURL(photoRes.data);
          setLivePhotoBlobUrl(blobUrl);
        } catch (err) {
          console.warn('Could not load live photo as blob, falling back to query token URL:', err);
        } finally {
          setLoadingPhoto(false);
        }
      }
    }
  };

  const openScheduleModal = async (verifId) => {
    const detail = await fetchVerificationDetail(verifId);
    if (detail) {
      if (detail.appointment) {
        setScheduleForm(prev => ({
          ...prev,
          location_name: detail.appointment.location_name || prev.location_name,
          venue_address: detail.appointment.venue_address || prev.venue_address,
          appointment_date: detail.appointment.appointment_date || todayStr,
          start_time: detail.appointment.start_time || '10:00',
          end_time: detail.appointment.end_time || '11:00',
          officer_name: detail.appointment.officer_name || prev.officer_name,
          officer_phone: detail.appointment.officer_phone || prev.officer_phone,
          instructions: detail.appointment.instructions || prev.instructions,
          reschedule_reason: '',
          admin_notes: detail.appointment.admin_notes || ''
        }));
      } else {
        setScheduleForm(prev => ({
          ...prev,
          appointment_date: todayStr,
          start_time: '10:00',
          end_time: '11:00',
          admin_notes: '',
          reschedule_reason: ''
        }));
      }
      setShowScheduleModal(true);
    }
  };

  const openManageModal = async (verifId, initialTab = 'details') => {
    const detail = await fetchVerificationDetail(verifId);
    if (detail) {
      if (detail.appointment) {
        setScheduleForm(prev => ({
          ...prev,
          location_name: detail.appointment.location_name || prev.location_name,
          venue_address: detail.appointment.venue_address || prev.venue_address,
          appointment_date: detail.appointment.appointment_date || todayStr,
          start_time: detail.appointment.start_time || '10:00',
          end_time: detail.appointment.end_time || '11:00',
          officer_name: detail.appointment.officer_name || prev.officer_name,
          officer_phone: detail.appointment.officer_phone || prev.officer_phone,
          instructions: detail.appointment.instructions || prev.instructions,
          reschedule_reason: '',
          admin_notes: detail.appointment.admin_notes || ''
        }));
      }
      setManageTab(initialTab);
      setShowManageModal(true);
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

  // 1. Stage 1: Approve Documents
  const handleApproveDocuments = async () => {
    if (!selectedVerif?.id) return;
    try {
      setProcessingAction(true);
      const token = localStorage.getItem('token');
      await axios.post(
        `${API}/admin/worker-verifications/${selectedVerif.id}/approve-documents`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('✓ Documents Approved! In-person verification can now be scheduled.');
      setShowConfirmApproveDocs(false);
      setShowReviewModal(false);
      fetchVerifications();
      // Directly offer to schedule
      openScheduleModal(selectedVerif.id);
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to approve documents'));
    } finally {
      setProcessingAction(false);
    }
  };

  // 2. Stage 1: Reject Documents
  const handleRejectDocuments = async () => {
    if (!selectedVerif?.id || !rejectionReason.trim()) return;
    try {
      setProcessingAction(true);
      const token = localStorage.getItem('token');
      await axios.post(
        `${API}/admin/worker-verifications/${selectedVerif.id}/reject`,
        { rejection_reason: rejectionReason.trim() },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('Worker documents rejected with reason');
      setShowRejectModal(false);
      setRejectionReason('');
      setShowReviewModal(false);
      setSelectedVerif(null);
      fetchVerifications();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to reject verification'));
    } finally {
      setProcessingAction(false);
    }
  };

  // 3. Stage 2: Schedule or Update In-Person Verification
  const handleScheduleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedVerif?.id) return;

    if (scheduleForm.end_time <= scheduleForm.start_time) {
      toast.error('End time must be later than start time.');
      return;
    }

    try {
      setProcessingAction(true);
      const token = localStorage.getItem('token');
      const hasActive = selectedVerif.appointment && 
        (selectedVerif.appointment.status === 'SCHEDULED' || selectedVerif.appointment.status === 'RESCHEDULED');

      const endpoint = hasActive
        ? `${API}/admin/worker-verifications/${selectedVerif.id}/appointment`
        : `${API}/admin/worker-verifications/${selectedVerif.id}/schedule-appointment`;

      const method = hasActive ? axios.put : axios.post;

      await method(
        endpoint,
        {
          location_name: scheduleForm.location_name,
          venue_address: scheduleForm.venue_address,
          appointment_date: scheduleForm.appointment_date,
          start_time: scheduleForm.start_time,
          end_time: scheduleForm.end_time,
          officer_name: scheduleForm.officer_name,
          officer_phone: scheduleForm.officer_phone,
          instructions: scheduleForm.instructions,
          admin_notes: scheduleForm.admin_notes
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success(hasActive 
        ? '✓ Appointment details updated successfully!' 
        : '📅 In-Person Verification appointment scheduled successfully!');
      setShowScheduleModal(false);
      setShowManageModal(false);
      fetchVerifications();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to save appointment'));
    } finally {
      setProcessingAction(false);
    }
  };

  // 4. Stage 2: Reschedule Appointment
  const handleRescheduleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedVerif?.id) return;

    if (scheduleForm.end_time <= scheduleForm.start_time) {
      toast.error('End time must be later than start time.');
      return;
    }
    if (!scheduleForm.reschedule_reason?.trim()) {
      toast.error('Please provide a reason for rescheduling.');
      return;
    }

    try {
      setProcessingAction(true);
      const token = localStorage.getItem('token');
      await axios.post(
        `${API}/admin/worker-verifications/${selectedVerif.id}/reschedule-appointment`,
        {
          appointment_date: scheduleForm.appointment_date,
          start_time: scheduleForm.start_time,
          end_time: scheduleForm.end_time,
          location_name: scheduleForm.location_name,
          venue_address: scheduleForm.venue_address,
          officer_name: scheduleForm.officer_name,
          officer_phone: scheduleForm.officer_phone,
          instructions: scheduleForm.instructions,
          reschedule_reason: scheduleForm.reschedule_reason.trim(),
          admin_notes: scheduleForm.admin_notes
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('✓ Appointment rescheduled successfully. Worker notified!');
      setShowManageModal(false);
      fetchVerifications();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to reschedule appointment'));
    } finally {
      setProcessingAction(false);
    }
  };

  // 5. Stage 2: Cancel Appointment
  const handleCancelSubmit = async () => {
    if (!selectedVerif?.id || !cancellationReason.trim()) return;

    try {
      setProcessingAction(true);
      const token = localStorage.getItem('token');
      await axios.post(
        `${API}/admin/worker-verifications/${selectedVerif.id}/cancel-appointment`,
        { cancellation_reason: cancellationReason.trim() },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('Appointment cancelled. Worker notified.');
      setShowCancelModal(false);
      setCancellationReason('');
      setShowManageModal(false);
      fetchVerifications();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to cancel appointment'));
    } finally {
      setProcessingAction(false);
    }
  };

  // 6. Stage 2: Record Outcome (PASSED, FAILED, NO_SHOW)
  const handleRecordOutcomeSubmit = async () => {
    if (!selectedVerif?.id) return;

    if (outcomeData.outcome !== 'PASSED' && !outcomeData.outcome_reason.trim()) {
      toast.error(`Please provide an outcome reason for ${outcomeData.outcome}.`);
      return;
    }

    try {
      setProcessingAction(true);
      const token = localStorage.getItem('token');
      const res = await axios.post(
        `${API}/admin/worker-verifications/${selectedVerif.id}/record-outcome`,
        {
          outcome: outcomeData.outcome,
          outcome_reason: outcomeData.outcome_reason.trim(),
          admin_notes: outcomeData.admin_notes.trim()
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      if (outcomeData.outcome === 'PASSED') {
        toast.success('🎉 Worker in-person check PASSED! Worker is now Fully Verified.');
      } else {
        toast.warning(`Outcome recorded as ${outcomeData.outcome}. Verification remains incomplete.`);
      }

      setShowRecordOutcomeModal(false);
      setShowManageModal(false);
      fetchVerifications();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to record outcome'));
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
            Worker Identity Verification &amp; Offline Scheduling
          </h1>
          <p className="text-sm text-gray-600">
            Two-stage verification: Review Aadhaar &amp; Labour certificates, then schedule and conduct in-person identity verification.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <span className="text-xs font-bold text-amber-800 bg-amber-100 px-3 py-1.5 rounded-full border border-amber-200">
            {verifications.filter(v => v.status === 'PENDING_VERIFICATION' || v.stage1_status === 'PENDING_REVIEW').length} Pending Docs
          </span>
          <span className="text-xs font-bold text-blue-800 bg-blue-100 px-3 py-1.5 rounded-full border border-blue-200">
            {verifications.filter(v => v.status === 'DOCUMENTS_APPROVED' && v.stage2_status === 'NOT_SCHEDULED').length} Awaiting Schedule
          </span>
        </div>
      </div>

      {/* Controls Bar: Search & Status Filters */}
      <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm flex flex-col md:flex-row justify-between gap-4">
        <form onSubmit={handleSearchSubmit} className="flex flex-1 max-w-md gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-gray-400 absolute left-3 top-3" />
            <input
              type="text"
              placeholder="Search worker name, phone, or trade..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full text-sm pl-9 pr-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
            />
          </div>
          <button type="submit" className="px-4 py-2 bg-orange-600 text-white rounded-lg text-sm font-bold hover:bg-orange-700">
            Search
          </button>
        </form>

        <div className="flex items-center space-x-2 overflow-x-auto pb-1">
          <Filter className="w-4 h-4 text-gray-500 flex-shrink-0" />
          <span className="text-xs font-bold text-gray-700">Filter:</span>
          {[
            { id: 'all', label: 'All' },
            { id: 'pending_verification', label: 'Docs Pending' },
            { id: 'documents_approved', label: 'Awaiting Schedule' },
            { id: 'in_person_scheduled', label: 'In-Person Scheduled' },
            { id: 'fully_verified', label: 'Fully Verified' },
            { id: 'incomplete', label: 'Incomplete / No-Show' },
            { id: 'rejected', label: 'Docs Rejected' }
          ].map((f) => (
            <button
              key={f.id}
              onClick={() => setStatusFilter(f.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold whitespace-nowrap transition ${
                statusFilter === f.id ? 'bg-orange-600 text-white shadow-sm' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* Verifications Table */}
      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-8 text-center flex justify-center">
            <Loader2 className="w-8 h-8 text-orange-500 animate-spin" />
          </div>
        ) : verifications.length === 0 ? (
          <div className="p-12 text-center text-gray-500 space-y-3">
            <ShieldCheck className="w-12 h-12 text-gray-300 mx-auto" />
            <p className="font-semibold">No Worker Verifications Found</p>
            <p className="text-xs text-gray-400">There are currently no worker verification submissions matching your filter.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-gray-50 text-xs font-bold text-gray-500 uppercase border-b border-gray-200">
                  <th className="py-3.5 px-4">Worker</th>
                  <th className="py-3.5 px-4">Stage 1: Documents</th>
                  <th className="py-3.5 px-4">Stage 2: In-Person Verification</th>
                  <th className="py-3.5 px-4">Overall Status</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 text-sm">
                {verifications.map((v) => {
                  const isDocsApproved = v.stage1_status === 'APPROVED';
                  const isScheduled = v.stage2_status === 'SCHEDULED' || v.stage2_status === 'RESCHEDULED';
                  const isFullyVerified = v.status === 'FULLY_VERIFIED' || v.status === 'VERIFIED';
                  const isFailedOrNoShow = v.stage2_status === 'FAILED' || v.stage2_status === 'NO_SHOW' || v.stage2_status === 'CANCELLED';

                  return (
                    <tr key={v.id} className="hover:bg-gray-50/80 transition">
                      <td className="py-3.5 px-4">
                        <div>
                          <p className="font-bold text-gray-900">{v.worker_name}</p>
                          <p className="text-xs text-gray-500">{v.worker_phone} • {v.worker_trade || 'General Worker'}</p>
                        </div>
                      </td>

                      {/* Stage 1: Document Review */}
                      <td className="py-3.5 px-4">
                        <div className="space-y-1">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-bold ${
                            v.stage1_status === 'APPROVED' ? 'bg-emerald-100 text-emerald-800' :
                            v.stage1_status === 'REJECTED' ? 'bg-rose-100 text-rose-800' :
                            'bg-amber-100 text-amber-800'
                          }`}>
                            {v.stage1_status === 'APPROVED' && <Check className="w-3 h-3 mr-1" />}
                            {v.stage1_status === 'REJECTED' && <XCircle className="w-3 h-3 mr-1" />}
                            {(!v.stage1_status || v.stage1_status === 'PENDING_REVIEW') && <Clock className="w-3 h-3 mr-1 animate-pulse" />}
                            {v.stage1_status === 'APPROVED' ? 'Approved' :
                             v.stage1_status === 'REJECTED' ? 'Rejected' : 'Pending Review'}
                          </span>
                          <div className="text-[11px] text-gray-400">
                            Aadhaar: •••• {v.aadhaar_last_four}
                          </div>
                        </div>
                      </td>

                      {/* Stage 2: In-Person Verification */}
                      <td className="py-3.5 px-4">
                        <div className="space-y-1">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-bold ${
                            v.stage2_status === 'PASSED' ? 'bg-emerald-100 text-emerald-800' :
                            v.stage2_status === 'SCHEDULED' ? 'bg-blue-100 text-blue-800' :
                            v.stage2_status === 'RESCHEDULED' ? 'bg-purple-100 text-purple-800' :
                            v.stage2_status === 'FAILED' ? 'bg-rose-100 text-rose-800' :
                            v.stage2_status === 'NO_SHOW' ? 'bg-amber-100 text-amber-900' :
                            v.stage2_status === 'CANCELLED' ? 'bg-gray-100 text-gray-700' :
                            'bg-slate-100 text-slate-600'
                          }`}>
                            {v.stage2_status === 'PASSED' && <CheckCircle className="w-3 h-3 mr-1" />}
                            {(v.stage2_status === 'SCHEDULED' || v.stage2_status === 'RESCHEDULED') && <Calendar className="w-3 h-3 mr-1" />}
                            {v.stage2_status || 'NOT_SCHEDULED'}
                          </span>

                          {v.appointment_date && (
                            <div className="text-[11px] text-gray-500 flex items-center">
                              <Calendar className="w-3 h-3 mr-1 text-gray-400" />
                              {v.appointment_date} {v.appointment_time ? `(${v.appointment_time})` : ''}
                            </div>
                          )}
                        </div>
                      </td>

                      {/* Overall Status */}
                      <td className="py-3.5 px-4">
                        <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-extrabold uppercase ${
                          isFullyVerified ? 'bg-emerald-100 text-emerald-800 border border-emerald-300' :
                          v.status === 'REJECTED' ? 'bg-rose-100 text-rose-800' :
                          v.status === 'DOCUMENTS_APPROVED' ? 'bg-sky-100 text-sky-800 border border-sky-200' :
                          isScheduled ? 'bg-purple-100 text-purple-800 border border-purple-200' :
                          'bg-amber-100 text-amber-900'
                        }`}>
                          {isFullyVerified ? '✓ Fully Verified' :
                           v.status === 'DOCUMENTS_APPROVED' ? 'Awaiting In-Person' :
                           v.status.replace(/_/g, ' ')}
                        </span>
                      </td>

                      {/* Actions */}
                      <td className="py-3.5 px-4 text-right space-x-2">
                        {/* Always allow viewing documents */}
                        <button
                          onClick={() => openReviewModal(v.id)}
                          className="px-2.5 py-1.5 border border-gray-300 text-gray-700 rounded-lg text-xs font-bold hover:bg-gray-50 inline-flex items-center"
                          title="Review Documents"
                        >
                          <Eye className="w-3.5 h-3.5 mr-1" />
                          Docs
                        </button>

                        {/* Scheduling Button: Enabled ONLY after documents are approved */}
                        {isDocsApproved && !isScheduled && !isFullyVerified && (
                          <button
                            onClick={() => openScheduleModal(v.id)}
                            className="px-3 py-1.5 bg-blue-600 text-white rounded-lg text-xs font-bold hover:bg-blue-700 shadow-sm transition inline-flex items-center"
                          >
                            <Calendar className="w-3.5 h-3.5 mr-1" />
                            Schedule In-Person
                          </button>
                        )}

                        {/* Manage Button: If an appointment is scheduled/rescheduled or has outcome */}
                        {(isScheduled || isFailedOrNoShow || v.appointment_date) && !isFullyVerified && (
                          <button
                            onClick={() => openManageModal(v.id)}
                            className="px-3 py-1.5 bg-purple-600 text-white rounded-lg text-xs font-bold hover:bg-purple-700 shadow-sm transition inline-flex items-center"
                          >
                            <Clock className="w-3.5 h-3.5 mr-1" />
                            Manage Appointment
                          </button>
                        )}

                        {/* Fully Verified View Button */}
                        {isFullyVerified && (
                          <button
                            onClick={() => openManageModal(v.id)}
                            className="px-3 py-1.5 bg-emerald-600 text-white rounded-lg text-xs font-bold hover:bg-emerald-700 shadow-sm transition inline-flex items-center"
                          >
                            <CheckCircle className="w-3.5 h-3.5 mr-1" />
                            Verified Record
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* =======================================================================
          MODAL 1: STAGE 1 DOCUMENT REVIEW MODAL
         ======================================================================= */}
      {showReviewModal && selectedVerif && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 max-w-2xl w-full shadow-2xl space-y-6 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-start border-b pb-3">
              <div>
                <span className="text-xs uppercase font-extrabold text-orange-600">Stage 1 — Document Verification</span>
                <h2 className="text-xl font-bold text-gray-900">{selectedVerif.worker_name}</h2>
                <p className="text-xs text-gray-500">Phone: {selectedVerif.worker_phone} • Trade: {selectedVerif.worker_trade}</p>
              </div>
              <button
                onClick={() => setShowReviewModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <XCircle className="w-6 h-6" />
              </button>
            </div>

            {/* Document Details Grid */}
            <div className="space-y-4">
              {/* Aadhaar */}
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

              {/* Labour Certificate */}
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

              {/* Live Photograph */}
              <div className="p-4 bg-purple-50/50 rounded-xl border border-purple-200 space-y-3">
                <div className="flex justify-between items-center">
                  <label className="text-xs font-bold text-gray-500 uppercase flex items-center">
                    <Camera className="w-4 h-4 mr-1 text-purple-600" />
                    Live Photograph (Worker Selfie)
                  </label>
                  {livePhotoBlobUrl && (
                    <span className="text-[11px] font-bold text-emerald-700 bg-emerald-100 px-2.5 py-0.5 rounded-full">
                      ✓ Authenticated View
                    </span>
                  )}
                </div>
                <div className="flex justify-center items-center min-h-[160px]">
                  {loadingPhoto ? (
                    <div className="flex flex-col items-center justify-center py-8 text-gray-400">
                      <Loader2 className="w-8 h-8 text-orange-500 animate-spin mb-2" />
                      <span className="text-xs">Loading live photo securely...</span>
                    </div>
                  ) : (
                    <img
                      src={livePhotoBlobUrl || `${API}${selectedVerif.live_photo_url}?token=${localStorage.getItem('token')}`}
                      alt="Live Photograph preview"
                      className="max-h-72 rounded-xl border border-gray-300 shadow-md object-cover"
                      onError={(e) => {
                        e.target.onerror = null;
                        e.target.src = 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=300&q=80';
                      }}
                    />
                  )}
                </div>
              </div>
            </div>

            {/* Stage 1 Actions */}
            <div className="pt-3 border-t flex flex-wrap gap-3">
              {selectedVerif.stage1_status !== 'APPROVED' ? (
                <>
                  <button
                    onClick={() => setShowRejectModal(true)}
                    className="flex-1 px-4 py-3 bg-red-600 text-white rounded-xl font-bold hover:bg-red-700 shadow-sm transition flex items-center justify-center"
                  >
                    <XCircle className="w-4 h-4 mr-2" />
                    Reject Documents
                  </button>

                  <button
                    onClick={() => setShowConfirmApproveDocs(true)}
                    className="flex-1 px-4 py-3 bg-emerald-600 text-white rounded-xl font-bold hover:bg-emerald-700 shadow-md transition flex items-center justify-center"
                  >
                    <CheckCircle className="w-5 h-5 mr-2" />
                    Approve Documents (Stage 1)
                  </button>
                </>
              ) : (
                <div className="w-full flex justify-between items-center bg-emerald-50 border border-emerald-200 p-4 rounded-xl">
                  <div className="flex items-center text-emerald-800 text-sm font-bold">
                    <CheckCircle className="w-5 h-5 mr-2 text-emerald-600" />
                    Stage 1 Documents are Approved.
                  </div>
                  <button
                    onClick={() => {
                      setShowReviewModal(false);
                      openScheduleModal(selectedVerif.id);
                    }}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg text-xs font-bold hover:bg-blue-700 flex items-center"
                  >
                    <Calendar className="w-4 h-4 mr-1.5" />
                    Schedule In-Person Verification
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* =======================================================================
          MODAL 2: STAGE 2 IN-PERSON SCHEDULING FORM
         ======================================================================= */}
      {showScheduleModal && selectedVerif && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 max-w-2xl w-full shadow-2xl space-y-6 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-start border-b pb-3">
              <div>
                <span className="text-xs uppercase font-extrabold text-blue-600">Stage 2 — In-Person Scheduling</span>
                <h2 className="text-xl font-bold text-gray-900">Schedule In-Person Verification</h2>
                <p className="text-xs text-gray-500">Worker: <span className="font-bold text-gray-800">{selectedVerif.worker_name}</span> ({selectedVerif.worker_phone})</p>
              </div>
              <button onClick={() => setShowScheduleModal(false)} className="text-gray-400 hover:text-gray-600">
                <XCircle className="w-6 h-6" />
              </button>
            </div>

            <form onSubmit={handleScheduleSubmit} className="space-y-4">
              {/* Location Name */}
              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Verification Center / Location Name *</label>
                <input
                  type="text"
                  required
                  value={scheduleForm.location_name}
                  onChange={(e) => setScheduleForm({ ...scheduleForm, location_name: e.target.value })}
                  placeholder="e.g. Sanyuth Central Verification Hub"
                  className="w-full p-2.5 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
              </div>

              {/* Venue Address */}
              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Complete Venue Address *</label>
                <textarea
                  required
                  rows={2}
                  value={scheduleForm.venue_address}
                  onChange={(e) => setScheduleForm({ ...scheduleForm, venue_address: e.target.value })}
                  placeholder="Street, Landmark, City, State, PIN"
                  className="w-full p-2.5 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
              </div>

              {/* Date & Time Slot */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-1">Appointment Date *</label>
                  <input
                    type="date"
                    required
                    min={todayStr}
                    value={scheduleForm.appointment_date}
                    onChange={(e) => setScheduleForm({ ...scheduleForm, appointment_date: e.target.value })}
                    className="w-full p-2.5 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-1">Start Time (24h) *</label>
                  <input
                    type="time"
                    required
                    value={scheduleForm.start_time}
                    onChange={(e) => setScheduleForm({ ...scheduleForm, start_time: e.target.value })}
                    className="w-full p-2.5 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-1">End Time (24h) *</label>
                  <input
                    type="time"
                    required
                    value={scheduleForm.end_time}
                    onChange={(e) => setScheduleForm({ ...scheduleForm, end_time: e.target.value })}
                    className="w-full p-2.5 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  />
                </div>
              </div>

              {/* Verification Officer Details */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-1">Assigned Verification Officer Name *</label>
                  <input
                    type="text"
                    required
                    value={scheduleForm.officer_name}
                    onChange={(e) => setScheduleForm({ ...scheduleForm, officer_name: e.target.value })}
                    placeholder="e.g. Ramesh Verma"
                    className="w-full p-2.5 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-1">Officer Contact Phone *</label>
                  <input
                    type="text"
                    required
                    value={scheduleForm.officer_phone}
                    onChange={(e) => setScheduleForm({ ...scheduleForm, officer_phone: e.target.value })}
                    placeholder="e.g. +91 98765 43210"
                    className="w-full p-2.5 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  />
                </div>
              </div>

              {/* Instructions for Worker */}
              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Instructions &amp; Required Documents for Worker *</label>
                <textarea
                  required
                  rows={2}
                  value={scheduleForm.instructions}
                  onChange={(e) => setScheduleForm({ ...scheduleForm, instructions: e.target.value })}
                  placeholder="List original documents and arrival instructions"
                  className="w-full p-2.5 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
              </div>

              {/* Optional Internal Admin Notes */}
              <div className="p-3 bg-amber-50 rounded-xl border border-amber-200">
                <label className="block text-xs font-bold text-amber-900 mb-1">Internal Admin Notes (Private — Not shown to Worker)</label>
                <textarea
                  rows={2}
                  value={scheduleForm.admin_notes}
                  onChange={(e) => setScheduleForm({ ...scheduleForm, admin_notes: e.target.value })}
                  placeholder="Notes for the assigned officer, specific checks needed, etc."
                  className="w-full p-2 border border-amber-300 rounded-lg text-sm bg-white focus:outline-none"
                />
              </div>

              <div className="pt-3 border-t flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowScheduleModal(false)}
                  className="px-4 py-2.5 border border-gray-300 text-gray-700 rounded-xl font-bold hover:bg-gray-50 text-sm"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={processingAction}
                  className="px-6 py-2.5 bg-blue-600 text-white rounded-xl font-bold hover:bg-blue-700 shadow-md transition flex items-center text-sm disabled:opacity-50"
                >
                  {processingAction ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Calendar className="w-4 h-4 mr-2" />}
                  {selectedVerif.appointment ? 'Save Appointment Details' : 'Confirm & Schedule Appointment'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* =======================================================================
          MODAL 3: MANAGE APPOINTMENT (OUTCOME, RESCHEDULE, CANCEL, HISTORY)
         ======================================================================= */}
      {showManageModal && selectedVerif && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 max-w-2xl w-full shadow-2xl space-y-6 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-start border-b pb-3">
              <div>
                <span className="text-xs uppercase font-extrabold text-purple-600">Appointment Management</span>
                <h2 className="text-xl font-bold text-gray-900">{selectedVerif.worker_name}</h2>
                <p className="text-xs text-gray-500">Phone: {selectedVerif.worker_phone} • Status: <span className="font-bold text-orange-600">{selectedVerif.status}</span></p>
              </div>
              <button onClick={() => setShowManageModal(false)} className="text-gray-400 hover:text-gray-600">
                <XCircle className="w-6 h-6" />
              </button>
            </div>

            {/* Navigation Tabs */}
            <div className="flex border-b text-xs font-bold space-x-2">
              <button
                onClick={() => setManageTab('details')}
                className={`py-2 px-3 border-b-2 transition ${
                  manageTab === 'details' ? 'border-purple-600 text-purple-700' : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                Appointment Details
              </button>
              {selectedVerif.status !== 'FULLY_VERIFIED' && selectedVerif.status !== 'VERIFIED' && (
                <>
                  <button
                    onClick={() => setManageTab('edit')}
                    className={`py-2 px-3 border-b-2 transition ${
                      manageTab === 'edit' ? 'border-purple-600 text-purple-700' : 'border-transparent text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    Edit Details
                  </button>
                  <button
                    onClick={() => setManageTab('outcome')}
                    className={`py-2 px-3 border-b-2 transition ${
                      manageTab === 'outcome' ? 'border-purple-600 text-purple-700' : 'border-transparent text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    Record Outcome
                  </button>
                  <button
                    onClick={() => setManageTab('reschedule')}
                    className={`py-2 px-3 border-b-2 transition ${
                      manageTab === 'reschedule' ? 'border-purple-600 text-purple-700' : 'border-transparent text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    Reschedule
                  </button>
                </>
              )}
              <button
                onClick={() => setManageTab('history')}
                className={`py-2 px-3 border-b-2 transition ${
                  manageTab === 'history' ? 'border-purple-600 text-purple-700' : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                Audit History
              </button>
            </div>

            {/* TAB 1: DETAILS */}
            {manageTab === 'details' && selectedVerif.appointment && (
              <div className="space-y-4">
                <div className="p-4 bg-purple-50/50 rounded-xl border border-purple-200 space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-xs uppercase font-extrabold text-purple-700">Appointment Information</span>
                    <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold uppercase ${
                      selectedVerif.appointment.status === 'PASSED' ? 'bg-emerald-100 text-emerald-800' :
                      selectedVerif.appointment.status === 'FAILED' ? 'bg-rose-100 text-rose-800' :
                      selectedVerif.appointment.status === 'NO_SHOW' ? 'bg-amber-100 text-amber-900' :
                      selectedVerif.appointment.status === 'CANCELLED' ? 'bg-gray-100 text-gray-800' :
                      'bg-blue-100 text-blue-800'
                    }`}>
                      {selectedVerif.appointment.status}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                    <div>
                      <span className="text-xs text-gray-500 font-semibold">Date &amp; Time:</span>
                      <p className="font-bold text-gray-900">{selectedVerif.appointment.appointment_date} ({selectedVerif.appointment.start_time} - {selectedVerif.appointment.end_time})</p>
                    </div>
                    <div>
                      <span className="text-xs text-gray-500 font-semibold">Location / Center:</span>
                      <p className="font-bold text-gray-900">{selectedVerif.appointment.location_name}</p>
                    </div>
                    <div className="md:col-span-2">
                      <span className="text-xs text-gray-500 font-semibold">Venue Address:</span>
                      <p className="font-medium text-gray-800">{selectedVerif.appointment.venue_address}</p>
                    </div>
                    <div>
                      <span className="text-xs text-gray-500 font-semibold">Verification Officer:</span>
                      <p className="font-bold text-gray-900">{selectedVerif.appointment.officer_name}</p>
                    </div>
                    <div>
                      <span className="text-xs text-gray-500 font-semibold">Officer Phone:</span>
                      <p className="font-bold text-gray-900">{selectedVerif.appointment.officer_phone}</p>
                    </div>
                    <div className="md:col-span-2">
                      <span className="text-xs text-gray-500 font-semibold">Worker Instructions:</span>
                      <p className="text-xs text-gray-700 bg-white p-2.5 rounded-lg border">{selectedVerif.appointment.instructions}</p>
                    </div>

                    {selectedVerif.appointment.admin_notes && (
                      <div className="md:col-span-2 p-3 bg-amber-50 rounded-lg border border-amber-200">
                        <span className="text-xs text-amber-900 font-bold">Internal Admin Notes:</span>
                        <p className="text-xs text-amber-800 mt-0.5">{selectedVerif.appointment.admin_notes}</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Actions if active */}
                {(selectedVerif.appointment.status === 'SCHEDULED' || selectedVerif.appointment.status === 'RESCHEDULED') && (
                  <div className="flex justify-between items-center pt-2">
                    <button
                      onClick={() => setManageTab('edit')}
                      className="px-4 py-2 border border-purple-300 text-purple-700 bg-purple-50/60 rounded-xl text-xs font-bold hover:bg-purple-100 flex items-center transition"
                    >
                      <Edit className="w-4 h-4 mr-1.5" />
                      Edit Details
                    </button>
                    <button
                      onClick={() => setShowCancelModal(true)}
                      className="px-4 py-2 border border-red-300 text-red-600 rounded-xl text-xs font-bold hover:bg-red-50 flex items-center"
                    >
                      <XCircle className="w-4 h-4 mr-1.5" />
                      Cancel This Appointment
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* TAB: EDIT DETAILS */}
            {manageTab === 'edit' && (
              <form onSubmit={handleScheduleSubmit} className="space-y-4">
                <p className="text-xs text-gray-500">Edit the center address, date, time slot, assigned officer, or instructions without creating duplicate appointments.</p>

                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-1">Center / Location Name *</label>
                  <input
                    type="text"
                    required
                    value={scheduleForm.location_name}
                    onChange={(e) => setScheduleForm({ ...scheduleForm, location_name: e.target.value })}
                    placeholder="e.g. Sanyuth Central Verification Hub"
                    className="w-full p-2.5 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-purple-500 focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-1">Complete Venue Address *</label>
                  <textarea
                    required
                    rows={2}
                    value={scheduleForm.venue_address}
                    onChange={(e) => setScheduleForm({ ...scheduleForm, venue_address: e.target.value })}
                    placeholder="Street, Landmark, City, State, PIN"
                    className="w-full p-2.5 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-purple-500 focus:outline-none"
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div>
                    <label className="block text-xs font-bold text-gray-700 mb-1">Appointment Date *</label>
                    <input
                      type="date"
                      required
                      value={scheduleForm.appointment_date}
                      onChange={(e) => setScheduleForm({ ...scheduleForm, appointment_date: e.target.value })}
                      className="w-full p-2.5 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-purple-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-gray-700 mb-1">Start Time (24h) *</label>
                    <input
                      type="time"
                      required
                      value={scheduleForm.start_time}
                      onChange={(e) => setScheduleForm({ ...scheduleForm, start_time: e.target.value })}
                      className="w-full p-2.5 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-purple-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-gray-700 mb-1">End Time (24h) *</label>
                    <input
                      type="time"
                      required
                      value={scheduleForm.end_time}
                      onChange={(e) => setScheduleForm({ ...scheduleForm, end_time: e.target.value })}
                      className="w-full p-2.5 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-purple-500 focus:outline-none"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-bold text-gray-700 mb-1">Assigned Verification Officer *</label>
                    <input
                      type="text"
                      required
                      value={scheduleForm.officer_name}
                      onChange={(e) => setScheduleForm({ ...scheduleForm, officer_name: e.target.value })}
                      placeholder="e.g. Ramesh Verma"
                      className="w-full p-2.5 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-purple-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-gray-700 mb-1">Officer Contact Phone *</label>
                    <input
                      type="text"
                      required
                      value={scheduleForm.officer_phone}
                      onChange={(e) => setScheduleForm({ ...scheduleForm, officer_phone: e.target.value })}
                      placeholder="e.g. +91 98765 43210"
                      className="w-full p-2.5 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-purple-500 focus:outline-none"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-1">Instructions for Worker</label>
                  <textarea
                    rows={2}
                    value={scheduleForm.instructions}
                    onChange={(e) => setScheduleForm({ ...scheduleForm, instructions: e.target.value })}
                    placeholder="List required physical documents and instructions"
                    className="w-full p-2.5 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-purple-500 focus:outline-none"
                  />
                </div>

                <div className="p-3 bg-amber-50 rounded-xl border border-amber-200">
                  <label className="block text-xs font-bold text-amber-900 mb-1">Internal Admin Notes (Private)</label>
                  <textarea
                    rows={2}
                    value={scheduleForm.admin_notes}
                    onChange={(e) => setScheduleForm({ ...scheduleForm, admin_notes: e.target.value })}
                    placeholder="Internal reference notes"
                    className="w-full p-2 border border-amber-300 rounded-lg text-sm bg-white focus:outline-none"
                  />
                </div>

                <div className="pt-2 flex justify-end space-x-2">
                  <button
                    type="button"
                    onClick={() => setManageTab('details')}
                    className="px-4 py-2 border border-gray-300 text-gray-700 rounded-xl text-sm font-bold hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={processingAction}
                    className="px-6 py-2 bg-purple-600 text-white rounded-xl text-sm font-bold hover:bg-purple-700 shadow flex items-center disabled:opacity-50"
                  >
                    {processingAction ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
                    Save Changes
                  </button>
                </div>
              </form>
            )}

            {/* TAB 2: RECORD OUTCOME */}
            {manageTab === 'outcome' && (
              <div className="space-y-4">
                <p className="text-xs text-gray-500">Record the actual result after the in-person appointment has taken place.</p>

                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-2">Verification Outcome *</label>
                  <div className="grid grid-cols-3 gap-3">
                    <button
                      type="button"
                      onClick={() => setOutcomeData({ ...outcomeData, outcome: 'PASSED' })}
                      className={`p-3 rounded-xl border text-center transition ${
                        outcomeData.outcome === 'PASSED' ? 'bg-emerald-50 border-emerald-500 text-emerald-800 font-bold ring-2 ring-emerald-400' : 'bg-gray-50 text-gray-700 hover:bg-gray-100'
                      }`}
                    >
                      <CheckCircle className="w-6 h-6 mx-auto mb-1 text-emerald-600" />
                      Passed
                    </button>

                    <button
                      type="button"
                      onClick={() => setOutcomeData({ ...outcomeData, outcome: 'FAILED' })}
                      className={`p-3 rounded-xl border text-center transition ${
                        outcomeData.outcome === 'FAILED' ? 'bg-rose-50 border-rose-500 text-rose-800 font-bold ring-2 ring-rose-400' : 'bg-gray-50 text-gray-700 hover:bg-gray-100'
                      }`}
                    >
                      <XCircle className="w-6 h-6 mx-auto mb-1 text-rose-600" />
                      Failed
                    </button>

                    <button
                      type="button"
                      onClick={() => setOutcomeData({ ...outcomeData, outcome: 'NO_SHOW' })}
                      className={`p-3 rounded-xl border text-center transition ${
                        outcomeData.outcome === 'NO_SHOW' ? 'bg-amber-50 border-amber-500 text-amber-900 font-bold ring-2 ring-amber-400' : 'bg-gray-50 text-gray-700 hover:bg-gray-100'
                      }`}
                    >
                      <Clock className="w-6 h-6 mx-auto mb-1 text-amber-600" />
                      No-Show
                    </button>
                  </div>
                </div>

                {outcomeData.outcome === 'PASSED' ? (
                  <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-900 space-y-1">
                    <p className="font-bold flex items-center">
                      <ShieldCheck className="w-4 h-4 mr-1 text-emerald-600" />
                      Confirming Fully Verified Status:
                    </p>
                    <p>Both Stage 1 (Documents) and Stage 2 (In-Person Check) will be marked complete. The worker profile will be granted full verified badge on the marketplace.</p>
                  </div>
                ) : (
                  <div>
                    <label className="block text-xs font-bold text-gray-700 mb-1">
                      Outcome Reason / Notes <span className="text-red-500">*</span>
                    </label>
                    <textarea
                      rows={3}
                      required
                      value={outcomeData.outcome_reason}
                      onChange={(e) => setOutcomeData({ ...outcomeData, outcome_reason: e.target.value })}
                      placeholder={outcomeData.outcome === 'FAILED' ? 'e.g. Identity photo mismatch or invalid original Aadhaar' : 'e.g. Worker did not attend the scheduled verification appointment'}
                      className="w-full p-2.5 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-purple-500 focus:outline-none"
                    />
                  </div>
                )}

                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-1">Internal Admin Notes (Optional)</label>
                  <textarea
                    rows={2}
                    value={outcomeData.admin_notes}
                    onChange={(e) => setOutcomeData({ ...outcomeData, admin_notes: e.target.value })}
                    placeholder="Internal reference notes"
                    className="w-full p-2.5 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-purple-500 focus:outline-none"
                  />
                </div>

                <div className="pt-2 flex justify-end">
                  <button
                    onClick={handleRecordOutcomeSubmit}
                    disabled={processingAction}
                    className="px-6 py-2.5 bg-purple-600 text-white rounded-xl text-sm font-bold hover:bg-purple-700 shadow flex items-center disabled:opacity-50"
                  >
                    {processingAction ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <CheckCircle className="w-4 h-4 mr-2" />}
                    Save Verification Outcome
                  </button>
                </div>
              </div>
            )}

            {/* TAB 3: RESCHEDULE */}
            {manageTab === 'reschedule' && (
              <form onSubmit={handleRescheduleSubmit} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div>
                    <label className="block text-xs font-bold text-gray-700 mb-1">New Date *</label>
                    <input
                      type="date"
                      required
                      min={todayStr}
                      value={scheduleForm.appointment_date}
                      onChange={(e) => setScheduleForm({ ...scheduleForm, appointment_date: e.target.value })}
                      className="w-full p-2.5 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-purple-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-gray-700 mb-1">New Start Time *</label>
                    <input
                      type="time"
                      required
                      value={scheduleForm.start_time}
                      onChange={(e) => setScheduleForm({ ...scheduleForm, start_time: e.target.value })}
                      className="w-full p-2.5 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-purple-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-gray-700 mb-1">New End Time *</label>
                    <input
                      type="time"
                      required
                      value={scheduleForm.end_time}
                      onChange={(e) => setScheduleForm({ ...scheduleForm, end_time: e.target.value })}
                      className="w-full p-2.5 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-purple-500 focus:outline-none"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-1">Reason for Rescheduling *</label>
                  <textarea
                    rows={2}
                    required
                    value={scheduleForm.reschedule_reason}
                    onChange={(e) => setScheduleForm({ ...scheduleForm, reschedule_reason: e.target.value })}
                    placeholder="e.g. Worker requested afternoon slot or verification officer unavailable"
                    className="w-full p-2.5 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-purple-500 focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-1">Internal Admin Notes (Optional)</label>
                  <input
                    type="text"
                    value={scheduleForm.admin_notes}
                    onChange={(e) => setScheduleForm({ ...scheduleForm, admin_notes: e.target.value })}
                    placeholder="Optional notes"
                    className="w-full p-2.5 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-purple-500 focus:outline-none"
                  />
                </div>

                <div className="pt-2 flex justify-end">
                  <button
                    type="submit"
                    disabled={processingAction}
                    className="px-6 py-2.5 bg-purple-600 text-white rounded-xl text-sm font-bold hover:bg-purple-700 shadow flex items-center disabled:opacity-50"
                  >
                    {processingAction ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <RefreshCw className="w-4 h-4 mr-2" />}
                    Confirm Reschedule
                  </button>
                </div>
              </form>
            )}

            {/* TAB 4: AUDIT HISTORY */}
            {manageTab === 'history' && (
              <div className="space-y-3">
                <p className="text-xs text-gray-500">Chronological history of scheduling, rescheduling, and status decisions.</p>
                {selectedVerif.appointment?.history && selectedVerif.appointment.history.length > 0 ? (
                  <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                    {selectedVerif.appointment.history.map((h, i) => (
                      <div key={i} className="p-3 bg-gray-50 border rounded-xl text-xs space-y-1">
                        <div className="flex justify-between items-center">
                          <span className="font-bold uppercase text-purple-700">{h.action}</span>
                          <span className="text-gray-400">{new Date(h.timestamp).toLocaleString()}</span>
                        </div>
                        {h.reason && (
                          <p className="text-gray-700"><span className="font-semibold">Reason:</span> {h.reason}</p>
                        )}
                        {h.outcome && (
                          <p className="text-gray-700"><span className="font-semibold">Outcome:</span> {h.outcome}</p>
                        )}
                        {h.notes && (
                          <p className="text-amber-700"><span className="font-semibold">Admin Notes:</span> {h.notes}</p>
                        )}
                        {h.details && (
                          <p className="text-gray-500 font-mono text-[11px]">{JSON.stringify(h.details)}</p>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-6 text-center text-xs text-gray-400">No previous appointment history recorded.</div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* =======================================================================
          CONFIRM APPROVE DOCUMENTS (STAGE 1) MODAL
         ======================================================================= */}
      {showConfirmApproveDocs && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-4 text-center">
            <div className="w-12 h-12 bg-emerald-100 rounded-full flex items-center justify-center mx-auto text-emerald-600">
              <CheckCircle className="w-7 h-7" />
            </div>
            <h3 className="text-lg font-bold text-gray-900">Approve Stage 1 Documents?</h3>
            <p className="text-sm text-gray-600">
              This will approve the worker&apos;s submitted Aadhaar details and Labour Certificate PDF. Stage 2 (In-Person Verification) scheduling will become available.
            </p>
            <div className="flex gap-3 pt-2">
              <button
                onClick={() => setShowConfirmApproveDocs(false)}
                className="flex-1 px-4 py-2.5 border border-gray-300 text-gray-700 rounded-xl font-bold hover:bg-gray-50 text-sm"
              >
                Cancel
              </button>
              <button
                onClick={handleApproveDocuments}
                disabled={processingAction}
                className="flex-1 px-4 py-2.5 bg-emerald-600 text-white rounded-xl font-bold hover:bg-emerald-700 shadow flex items-center justify-center text-sm disabled:opacity-50"
              >
                {processingAction ? <Loader2 className="w-4 h-4 mr-1 animate-spin" /> : null}
                Approve &amp; Continue
              </button>
            </div>
          </div>
        </div>
      )}

      {/* =======================================================================
          REJECT DOCUMENTS MODAL
         ======================================================================= */}
      {showRejectModal && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <div className="flex justify-between items-center border-b pb-2">
              <h3 className="text-lg font-bold text-gray-900">Reject Worker Documents</h3>
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
                placeholder="e.g. Labour certificate signature is unclear. Please re-upload a clear PDF document."
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
                onClick={handleRejectDocuments}
                disabled={processingAction || !rejectionReason.trim()}
                className="flex-1 px-4 py-2.5 bg-red-600 text-white rounded-xl text-xs font-bold hover:bg-red-700 shadow disabled:opacity-50"
              >
                {processingAction ? 'Rejecting...' : 'Reject Documents'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* =======================================================================
          CANCEL APPOINTMENT MODAL
         ======================================================================= */}
      {showCancelModal && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <div className="flex justify-between items-center border-b pb-2">
              <h3 className="text-lg font-bold text-gray-900">Cancel Appointment</h3>
              <button onClick={() => setShowCancelModal(false)} className="text-gray-400 hover:text-gray-600">
                <XCircle className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-gray-600">Provide a reason for cancellation. The worker will be notified and a new appointment can be arranged.</p>

            <div>
              <label className="block text-xs font-bold text-gray-700 mb-1">Cancellation Reason *</label>
              <textarea
                value={cancellationReason}
                onChange={(e) => setCancellationReason(e.target.value)}
                placeholder="e.g. Center closed for emergency maintenance or worker requested cancellation."
                rows={3}
                className="w-full p-3 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-red-500 focus:outline-none"
              />
            </div>

            <div className="flex gap-3 pt-2">
              <button
                onClick={() => setShowCancelModal(false)}
                className="flex-1 px-4 py-2.5 border border-gray-300 text-gray-700 rounded-xl text-xs font-bold hover:bg-gray-50"
              >
                Go Back
              </button>
              <button
                onClick={handleCancelSubmit}
                disabled={processingAction || !cancellationReason.trim()}
                className="flex-1 px-4 py-2.5 bg-red-600 text-white rounded-xl text-xs font-bold hover:bg-red-700 shadow disabled:opacity-50"
              >
                {processingAction ? 'Cancelling...' : 'Confirm Cancellation'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* =======================================================================
          PDF VIEWER MODAL
         ======================================================================= */}
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

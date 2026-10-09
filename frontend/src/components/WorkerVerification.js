import React, { useState, useEffect, useRef } from 'react';
import { 
  ShieldCheck, 
  FileText, 
  Camera, 
  CheckCircle2, 
  AlertCircle, 
  ArrowRight, 
  ArrowLeft, 
  Upload, 
  RefreshCw, 
  Trash2, 
  Eye, 
  Lock, 
  User, 
  Phone, 
  Mail, 
  Clock, 
  XCircle,
  Loader2
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';
import { API, getErrorMessage } from '../lib/api';

export const WorkerVerification = ({ currentUser, onVerificationChange }) => {
  const [step, setStep] = useState(1); // 1: Personal, 2: Identity, 3: Review, 4: Status
  const [statusData, setStatusData] = useState(null);
  const [loading, setLoading] = useState(true);

  // Form State
  const [aadhaarRaw, setAadhaarRaw] = useState('');
  const [certFile, setCertFile] = useState(null); // { filename, original_name }
  const [photoFile, setPhotoFile] = useState(null); // { filename, original_name, dataUrl }

  // Uploading / Camera States
  const [uploadingCert, setUploadingCert] = useState(false);
  const [uploadingPhoto, setUploadingPhoto] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [isCameraOpen, setIsCameraOpen] = useState(false);
  const videoRef = useRef(null);
  const streamRef = useRef(null);

  useEffect(() => {
    fetchVerificationStatus();
  }, []);

  const fetchVerificationStatus = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const res = await axios.get(`${API}/worker/verification/status`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStatusData(res.data);
      if (onVerificationChange) {
        onVerificationChange(res.data);
      }
      if (res.data?.status && res.data.status !== 'NOT_SUBMITTED') {
        setStep(4); // Go straight to Status View
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Aadhaar input formatting
  const handleAadhaarChange = (e) => {
    const rawDigits = e.target.value.replace(/\D/g, '').slice(0, 12);
    // Format with spaces XXXX XXXX XXXX
    const formatted = rawDigits.replace(/(\d{4})(?=\d)/g, '$1 ').trim();
    setAadhaarRaw(formatted);
  };

  const cleanAadhaar = aadhaarRaw.replace(/\D/g, '');
  const isAadhaarValid = cleanAadhaar.length === 12;
  const maskedAadhaarDisplay = isAadhaarValid ? `XXXX XXXX ${cleanAadhaar.slice(8)}` : '';

  // Labour Certificate Upload Handler
  const handleCertSelect = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
      toast.error('Only PDF files are allowed for Labour Certificate.');
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      toast.error('PDF file size must be less than 10MB.');
      return;
    }

    try {
      setUploadingCert(true);
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('file', file);

      const res = await axios.post(`${API}/worker/verification/upload-doc?doc_type=labour_certificate`, formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      });

      setCertFile({
        filename: res.data.filename,
        original_name: res.data.original_name || file.name
      });
      toast.success('Labour Certificate PDF uploaded successfully!');
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to upload Labour Certificate PDF'));
    } finally {
      setUploadingCert(false);
    }
  };

  // Camera Handlers for Live Photograph
  const startCamera = async () => {
    setIsCameraOpen(true);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: "user" } 
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch (err) {
      console.error(err);
      toast.error('Unable to access camera. You can also upload a photo file.');
      setIsCameraOpen(false);
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setIsCameraOpen(false);
  };

  const capturePhoto = () => {
    if (!videoRef.current) return;

    const canvas = document.createElement('canvas');
    canvas.width = videoRef.current.videoWidth || 640;
    canvas.height = videoRef.current.videoHeight || 480;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);

    canvas.toBlob(async (blob) => {
      if (!blob) return;
      const file = new File([blob], "live_photo.jpg", { type: "image/jpeg" });
      await uploadPhotoFile(file, canvas.toDataURL('image/jpeg'));
      stopCamera();
    }, 'image/jpeg', 0.9);
  };

  const handlePhotoFileSelect = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      toast.error('Please select a valid image file (JPG, PNG, WEBP).');
      return;
    }

    const reader = new FileReader();
    reader.onload = async (event) => {
      await uploadPhotoFile(file, event.target.result);
    };
    reader.readAsDataURL(file);
  };

  const uploadPhotoFile = async (file, dataUrl) => {
    try {
      setUploadingPhoto(true);
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('file', file);

      const res = await axios.post(`${API}/worker/verification/upload-doc?doc_type=live_photo`, formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      });

      setPhotoFile({
        filename: res.data.filename,
        original_name: res.data.original_name || file.name,
        dataUrl: dataUrl
      });
      toast.success('Live Photograph captured and uploaded!');
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to upload Live Photo'));
    } finally {
      setUploadingPhoto(false);
    }
  };

  // Submit Handler
  const handleSubmitVerification = async () => {
    if (!isAadhaarValid) {
      toast.error('Please enter a valid 12-digit Aadhaar number.');
      return;
    }
    if (!certFile?.filename) {
      toast.error('Please upload your Labour Certificate PDF.');
      return;
    }
    if (!photoFile?.filename) {
      toast.error('Please capture/upload your Live Photograph.');
      return;
    }

    try {
      setSubmitting(true);
      const token = localStorage.getItem('token');
      const res = await axios.post(
        `${API}/worker/verification/submit`,
        {
          aadhaar_number: cleanAadhaar,
          labour_certificate_filename: certFile.filename,
          labour_certificate_name: certFile.original_name,
          live_photo_filename: photoFile.filename
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      toast.success('🎉 Identity verification submitted for Admin review!');
      setStatusData(res.data);
      if (onVerificationChange) {
        onVerificationChange(res.data);
      }
      setStep(4);
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to submit identity verification'));
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="p-8 text-center flex justify-center">
        <Loader2 className="w-10 h-10 text-orange-500 animate-spin" />
      </div>
    );
  }

  // STEP 4: STATUS VIEW (PENDING, VERIFIED, REJECTED)
  if (step === 4 && statusData && statusData.status !== 'NOT_SUBMITTED') {
    const isPending = statusData.status === 'PENDING_VERIFICATION';
    const isVerified = statusData.status === 'VERIFIED';
    const isRejected = statusData.status === 'REJECTED';

    return (
      <div className="max-w-3xl mx-auto p-6 space-y-6">
        {/* Status Header Banner */}
        <div className={`p-6 rounded-2xl border text-white shadow-lg ${
          isVerified ? 'bg-gradient-to-r from-emerald-600 to-teal-600 border-emerald-500' :
          isRejected ? 'bg-gradient-to-r from-red-600 to-rose-600 border-red-500' :
          'bg-gradient-to-r from-amber-500 to-orange-600 border-amber-400'
        }`}>
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-white/20 rounded-xl backdrop-blur-md">
              {isVerified ? <ShieldCheck className="w-8 h-8 text-white" /> :
               isRejected ? <XCircle className="w-8 h-8 text-white" /> :
               <Clock className="w-8 h-8 text-white animate-pulse" />}
            </div>
            <div>
              <span className="text-xs uppercase font-extrabold tracking-wider opacity-90">Worker Identity Status</span>
              <h1 className="text-2xl font-bold">
                {isVerified ? '✓ Identity Verified' :
                 isRejected ? '✕ Verification Rejected' :
                 'Verification Pending'}
              </h1>
              <p className="text-sm opacity-90 mt-1">
                {isVerified ? 'Your account has been fully verified by Sanyuth Admin.' :
                 isRejected ? 'Action required: Your submitted documents need changes.' :
                 'Your identity documents have been submitted and are under admin review.'}
              </p>
            </div>
          </div>
        </div>

        {/* Rejection Alert & Resubmit Trigger */}
        {isRejected && (
          <div className="bg-red-50 border border-red-200 p-5 rounded-2xl space-y-3">
            <div className="flex items-start space-x-3 text-red-800">
              <AlertCircle className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-bold text-base">Rejection Reason</h3>
                <p className="text-sm mt-1">{statusData.rejection_reason || 'Documents provided were unclear or incomplete.'}</p>
              </div>
            </div>
            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setStep(2)}
                className="px-5 py-2.5 bg-red-600 text-white rounded-xl text-sm font-bold shadow hover:bg-red-700 transition flex items-center"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Resubmit Verification Documents
              </button>
            </div>
          </div>
        )}

        {/* Submitted Summary Card */}
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 space-y-4">
          <h3 className="text-lg font-bold text-gray-900 border-b pb-3 flex items-center">
            <ShieldCheck className="w-5 h-5 text-orange-600 mr-2" />
            Submitted Verification Details
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-gray-50 rounded-xl border border-gray-100 space-y-1">
              <div className="text-xs text-gray-500 font-semibold uppercase">Aadhaar Card</div>
              <div className="text-base font-bold text-gray-900 flex items-center">
                <Lock className="w-4 h-4 text-emerald-600 mr-1.5" />
                XXXX XXXX {statusData.aadhaar_last_four || 'XXXX'}
              </div>
              <span className="text-[11px] text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded font-bold inline-block">
                ✓ Masked & Secured
              </span>
            </div>

            <div className="p-4 bg-gray-50 rounded-xl border border-gray-100 space-y-1">
              <div className="text-xs text-gray-500 font-semibold uppercase">Labour Certificate</div>
              <div className="text-sm font-bold text-gray-900 truncate">
                {statusData.labour_certificate_name || 'labour_certificate.pdf'}
              </div>
              <span className="text-[11px] text-blue-700 bg-blue-100 px-2 py-0.5 rounded font-bold inline-block">
                ✓ PDF Uploaded
              </span>
            </div>

            <div className="p-4 bg-gray-50 rounded-xl border border-gray-100 space-y-1">
              <div className="text-xs text-gray-500 font-semibold uppercase">Live Photograph</div>
              <div className="text-sm font-bold text-gray-900 flex items-center">
                <Camera className="w-4 h-4 text-purple-600 mr-1.5" />
                Live Photo Capture
              </div>
              <span className="text-[11px] text-purple-700 bg-purple-100 px-2 py-0.5 rounded font-bold inline-block">
                ✓ Photo Saved
              </span>
            </div>
          </div>

          <div className="text-xs text-gray-500 pt-2 border-t flex justify-between items-center">
            <span>Submitted: {statusData.submitted_at ? new Date(statusData.submitted_at).toLocaleString() : 'N/A'}</span>
            <span className="font-semibold capitalize text-orange-600">Status: {statusData.status}</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-6">
      {/* Wizard Header */}
      <div className="bg-gradient-to-r from-orange-600 to-amber-600 p-6 rounded-2xl text-white shadow-xl flex flex-wrap justify-between items-center gap-4">
        <div className="flex items-center space-x-3">
          <div className="p-3 bg-white/20 rounded-xl backdrop-blur-md">
            <ShieldCheck className="w-7 h-7 text-white" />
          </div>
          <div>
            <span className="text-xs uppercase font-extrabold tracking-wider text-orange-100">Verification Wizard</span>
            <h1 className="text-2xl font-bold">Worker Identity Verification</h1>
            <p className="text-xs text-orange-100 mt-0.5">Submit your official Aadhaar and Labour documents to become a verified worker on Sanyuth.</p>
          </div>
        </div>
      </div>

      {/* Progress Steps Indicator */}
      <div className="flex items-center justify-between bg-white p-4 rounded-xl border border-gray-200 shadow-sm text-sm font-bold">
        <div className={`flex items-center space-x-2 ${step >= 1 ? 'text-orange-600' : 'text-gray-400'}`}>
          <span className={`w-7 h-7 rounded-full flex items-center justify-center text-xs ${step >= 1 ? 'bg-orange-600 text-white' : 'bg-gray-200 text-gray-600'}`}>1</span>
          <span>Personal Info</span>
        </div>
        <ArrowRight className="w-4 h-4 text-gray-300" />
        <div className={`flex items-center space-x-2 ${step >= 2 ? 'text-orange-600' : 'text-gray-400'}`}>
          <span className={`w-7 h-7 rounded-full flex items-center justify-center text-xs ${step >= 2 ? 'bg-orange-600 text-white' : 'bg-gray-200 text-gray-600'}`}>2</span>
          <span>Documents & Photo</span>
        </div>
        <ArrowRight className="w-4 h-4 text-gray-300" />
        <div className={`flex items-center space-x-2 ${step >= 3 ? 'text-orange-600' : 'text-gray-400'}`}>
          <span className={`w-7 h-7 rounded-full flex items-center justify-center text-xs ${step >= 3 ? 'bg-orange-600 text-white' : 'bg-gray-200 text-gray-600'}`}>3</span>
          <span>Review & Submit</span>
        </div>
      </div>

      {/* STEP 1: PERSONAL DETAILS */}
      {step === 1 && (
        <div className="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm space-y-6">
          <h2 className="text-lg font-bold text-gray-900 border-b pb-3">Step 1 — Confirm Personal Details</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-gray-50 rounded-xl space-y-1 border">
              <label className="text-xs font-bold text-gray-500 uppercase flex items-center">
                <User className="w-3.5 h-3.5 mr-1 text-gray-400" /> Full Name
              </label>
              <p className="text-base font-bold text-gray-900">{currentUser?.name || 'Worker User'}</p>
            </div>

            <div className="p-4 bg-gray-50 rounded-xl space-y-1 border">
              <label className="text-xs font-bold text-gray-500 uppercase flex items-center">
                <Phone className="w-3.5 h-3.5 mr-1 text-gray-400" /> Phone Number
              </label>
              <p className="text-base font-bold text-gray-900">{currentUser?.phone || 'N/A'}</p>
            </div>

            <div className="p-4 bg-gray-50 rounded-xl space-y-1 border">
              <label className="text-xs font-bold text-gray-500 uppercase flex items-center">
                <Mail className="w-3.5 h-3.5 mr-1 text-gray-400" /> Email
              </label>
              <p className="text-base font-bold text-gray-900">{currentUser?.email || 'Not provided'}</p>
            </div>

            <div className="p-4 bg-gray-50 rounded-xl space-y-1 border">
              <label className="text-xs font-bold text-gray-500 uppercase flex items-center">
                <ShieldCheck className="w-3.5 h-3.5 mr-1 text-gray-400" /> Registered Role
              </label>
              <p className="text-base font-bold text-orange-600 uppercase">{currentUser?.role || 'worker'}</p>
            </div>
          </div>

          <div className="flex justify-end pt-4 border-t">
            <button
              onClick={() => setStep(2)}
              className="px-6 py-3 bg-orange-600 text-white rounded-xl font-bold shadow hover:bg-orange-700 transition flex items-center"
            >
              Next: Identity Verification
              <ArrowRight className="w-4 h-4 ml-2" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 2: IDENTITY VERIFICATION FORM */}
      {step === 2 && (
        <div className="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm space-y-6">
          <div>
            <h2 className="text-lg font-bold text-gray-900">Step 2 — Identity Verification Documents</h2>
            <p className="text-xs text-gray-500 mt-1">Submit your 12-digit Aadhaar number, Labour Certificate PDF, and Live Photograph.</p>
          </div>

          {/* 1. Aadhaar Number Input */}
          <div className="p-5 bg-orange-50/50 rounded-2xl border border-orange-200 space-y-3">
            <label className="block text-sm font-bold text-gray-900">
              1. Aadhaar Card Number <span className="text-red-500">*</span>
            </label>

            <div className="relative max-w-md">
              <input
                type="text"
                value={aadhaarRaw}
                onChange={handleAadhaarChange}
                placeholder="XXXX XXXX XXXX"
                maxLength={14}
                className="w-full text-lg font-mono font-bold tracking-wider px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-orange-500 bg-white"
              />
              {isAadhaarValid && (
                <CheckCircle2 className="w-6 h-6 text-emerald-600 absolute right-3 top-3.5" />
              )}
            </div>

            {maskedAadhaarDisplay && (
              <p className="text-xs font-bold text-emerald-700 flex items-center">
                <Lock className="w-3.5 h-3.5 mr-1" />
                Will be stored and displayed as: {maskedAadhaarDisplay}
              </p>
            )}

            <div className="bg-white p-3 rounded-xl border text-xs text-gray-600 flex items-start space-x-2">
              <Lock className="w-4 h-4 text-orange-600 flex-shrink-0 mt-0.5" />
              <span>
                <strong>Privacy Note:</strong> Your Aadhaar information is sensitive and will only be used for worker verification. Full Aadhaar is never exposed publicly.
              </span>
            </div>
          </div>

          {/* 2. Labour Certificate Upload */}
          <div className="p-5 bg-blue-50/40 rounded-2xl border border-blue-200 space-y-3">
            <label className="block text-sm font-bold text-gray-900">
              2. Labour Certificate (PDF Format) <span className="text-red-500">*</span>
            </label>
            <p className="text-xs text-gray-500">Upload your government-issued labour or trade certificate in PDF format (Max 10MB).</p>

            {certFile ? (
              <div className="bg-white p-4 rounded-xl border border-emerald-300 flex justify-between items-center">
                <div className="flex items-center space-x-3">
                  <FileText className="w-8 h-8 text-rose-600" />
                  <div>
                    <p className="text-sm font-bold text-gray-900">{certFile.original_name}</p>
                    <span className="text-xs font-bold text-emerald-700">✓ PDF Uploaded Successfully</span>
                  </div>
                </div>
                <div className="flex space-x-2">
                  <label className="px-3 py-1.5 border border-gray-300 rounded-lg text-xs font-bold hover:bg-gray-50 cursor-pointer">
                    Replace
                    <input type="file" accept=".pdf,application/pdf" onChange={handleCertSelect} className="hidden" />
                  </label>
                  <button
                    onClick={() => setCertFile(null)}
                    className="p-1.5 text-red-600 hover:bg-red-50 rounded-lg"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ) : (
              <label className="border-2 border-dashed border-blue-300 rounded-2xl p-6 flex flex-col items-center justify-center cursor-pointer hover:bg-blue-50/80 transition bg-white text-center">
                {uploadingCert ? (
                  <Loader2 className="w-8 h-8 text-blue-600 animate-spin mb-2" />
                ) : (
                  <Upload className="w-8 h-8 text-blue-600 mb-2" />
                )}
                <span className="text-sm font-bold text-blue-900">Click to Select Labour Certificate PDF</span>
                <span className="text-xs text-gray-400 mt-1">Accepts PDF files up to 10MB</span>
                <input type="file" accept=".pdf,application/pdf" onChange={handleCertSelect} className="hidden" disabled={uploadingCert} />
              </label>
            )}
          </div>

          {/* 3. Live Photograph Capture */}
          <div className="p-5 bg-purple-50/40 rounded-2xl border border-purple-200 space-y-3">
            <label className="block text-sm font-bold text-gray-900">
              3. Live Photograph <span className="text-red-500">*</span>
            </label>
            <p className="text-xs text-gray-500">Take a current photograph of yourself using your device camera for worker verification.</p>

            {photoFile ? (
              <div className="bg-white p-4 rounded-xl border border-emerald-300 flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  {photoFile.dataUrl ? (
                    <img src={photoFile.dataUrl} alt="Captured preview" className="w-16 h-16 rounded-xl object-cover border" />
                  ) : (
                    <Camera className="w-10 h-10 text-purple-600" />
                  )}
                  <div>
                    <p className="text-sm font-bold text-gray-900">Live Photograph</p>
                    <span className="text-xs font-bold text-emerald-700">✓ Photo Captured & Uploaded</span>
                  </div>
                </div>
                <button
                  onClick={() => setPhotoFile(null)}
                  className="px-3 py-1.5 border border-gray-300 text-xs font-bold rounded-lg hover:bg-gray-50"
                >
                  Retake Photo
                </button>
              </div>
            ) : isCameraOpen ? (
              <div className="bg-black rounded-2xl p-4 flex flex-col items-center space-y-3">
                <video ref={videoRef} autoPlay playsInline className="w-full max-w-sm rounded-xl border border-gray-700" />
                <div className="flex space-x-3">
                  <button
                    onClick={capturePhoto}
                    disabled={uploadingPhoto}
                    className="px-5 py-2.5 bg-orange-600 text-white rounded-xl text-sm font-bold hover:bg-orange-700 flex items-center"
                  >
                    <Camera className="w-4 h-4 mr-2" />
                    {uploadingPhoto ? 'Capturing...' : 'Capture Photo'}
                  </button>
                  <button
                    onClick={stopCamera}
                    className="px-4 py-2.5 bg-gray-800 text-white rounded-xl text-sm font-bold hover:bg-gray-700"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex flex-wrap gap-3">
                <button
                  onClick={startCamera}
                  className="px-5 py-3 bg-purple-600 text-white rounded-xl text-sm font-bold hover:bg-purple-700 transition flex items-center shadow"
                >
                  <Camera className="w-4 h-4 mr-2" />
                  Open Camera
                </button>

                <label className="px-5 py-3 border border-purple-300 text-purple-700 bg-white hover:bg-purple-50 rounded-xl text-sm font-bold cursor-pointer transition flex items-center">
                  <Upload className="w-4 h-4 mr-2" />
                  Upload Photo File
                  <input type="file" accept="image/*" onChange={handlePhotoFileSelect} className="hidden" />
                </label>
              </div>
            )}
          </div>

          {/* Navigation Buttons */}
          <div className="flex justify-between pt-4 border-t">
            <button
              onClick={() => setStep(1)}
              className="px-4 py-2.5 border border-gray-300 text-gray-700 rounded-xl font-bold hover:bg-gray-50 flex items-center"
            >
              <ArrowLeft className="w-4 h-4 mr-2" /> Back
            </button>

            <button
              onClick={() => setStep(3)}
              disabled={!isAadhaarValid || !certFile || !photoFile}
              className="px-6 py-2.5 bg-orange-600 text-white rounded-xl font-bold shadow hover:bg-orange-700 transition disabled:opacity-50 flex items-center"
            >
              Next: Review
              <ArrowRight className="w-4 h-4 ml-2" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 3: REVIEW STEP */}
      {step === 3 && (
        <div className="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm space-y-6">
          <div>
            <h2 className="text-lg font-bold text-gray-900">Step 3 — Review Identity Verification</h2>
            <p className="text-xs text-gray-500 mt-1">Review your details carefully before submitting for Sanyuth Admin approval.</p>
          </div>

          <div className="space-y-4">
            {/* Aadhaar Summary */}
            <div className="p-4 bg-gray-50 rounded-xl border flex justify-between items-center">
              <div>
                <span className="text-xs font-bold text-gray-500 uppercase">Aadhaar Card Number</span>
                <p className="text-base font-bold text-gray-900 flex items-center mt-0.5">
                  <Lock className="w-4 h-4 text-emerald-600 mr-1.5" />
                  {maskedAadhaarDisplay}
                </p>
              </div>
              <span className="text-xs font-bold text-emerald-700 bg-emerald-100 px-3 py-1 rounded-full">
                ✓ Added
              </span>
            </div>

            {/* Labour Cert Summary */}
            <div className="p-4 bg-gray-50 rounded-xl border flex justify-between items-center">
              <div>
                <span className="text-xs font-bold text-gray-500 uppercase">Labour Certificate PDF</span>
                <p className="text-sm font-bold text-gray-900 flex items-center mt-0.5">
                  <FileText className="w-4 h-4 text-rose-600 mr-1.5" />
                  {certFile?.original_name}
                </p>
              </div>
              <span className="text-xs font-bold text-emerald-700 bg-emerald-100 px-3 py-1 rounded-full">
                ✓ Uploaded
              </span>
            </div>

            {/* Live Photo Summary */}
            <div className="p-4 bg-gray-50 rounded-xl border flex justify-between items-center">
              <div className="flex items-center space-x-3">
                {photoFile?.dataUrl ? (
                  <img src={photoFile.dataUrl} alt="Live captured thumbnail" className="w-14 h-14 rounded-xl object-cover border" />
                ) : (
                  <Camera className="w-8 h-8 text-purple-600" />
                )}
                <div>
                  <span className="text-xs font-bold text-gray-500 uppercase">Live Photograph</span>
                  <p className="text-sm font-bold text-gray-900">Current Selfie Photo</p>
                </div>
              </div>
              <span className="text-xs font-bold text-emerald-700 bg-emerald-100 px-3 py-1 rounded-full">
                ✓ Captured
              </span>
            </div>
          </div>

          {/* Submission Notice */}
          <div className="p-4 bg-amber-50 rounded-xl border border-amber-200 text-xs text-amber-900 space-y-1">
            <p className="font-bold">⚠️ Before Submitting:</p>
            <p>Your worker profile status will become <strong>Verification Pending</strong>. Admin officers will review your Labour Certificate PDF and Live Photograph against your registered details before verifying your account.</p>
          </div>

          <div className="flex justify-between pt-4 border-t">
            <button
              onClick={() => setStep(2)}
              className="px-4 py-2.5 border border-gray-300 text-gray-700 rounded-xl font-bold hover:bg-gray-50 flex items-center"
            >
              <ArrowLeft className="w-4 h-4 mr-2" /> Back
            </button>

            <button
              onClick={handleSubmitVerification}
              disabled={submitting}
              className="px-6 py-3 bg-orange-600 text-white rounded-xl font-bold shadow-md hover:bg-orange-700 transition flex items-center disabled:opacity-50"
            >
              {submitting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" /> Submitting...
                </>
              ) : (
                <>
                  <ShieldCheck className="w-5 h-5 mr-2" /> Submit for Verification
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

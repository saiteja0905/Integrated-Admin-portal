import React, { useState, useEffect } from 'react';
import { 
  Heart, 
  User, 
  Phone, 
  MapPin, 
  Globe, 
  Plus, 
  Trash2, 
  ShieldAlert, 
  KeyRound, 
  Camera, 
  HelpCircle, 
  CheckCircle2, 
  Clock, 
  Truck
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';
import { API, getErrorMessage } from '../lib/api';

export const FamilyMode = ({ onSelectAddressForBooking }) => {
  const [addresses, setAddresses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [formData, setFormData] = useState({
    parent_name: '',
    parent_phone: '',
    address: '',
    city: 'Hyderabad',
    preferred_language: 'Telugu',
    landmark: ''
  });
  const [activeTab, setActiveTab] = useState('addresses'); // 'addresses' or 'live_tracking'
  const [activeJobId, setActiveJobId] = useState('');
  const [trackingData, setTrackingData] = useState(null);
  const [otpInput, setOtpInput] = useState('');

  useEffect(() => {
    fetchAddresses();
  }, []);

  const fetchAddresses = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const res = await axios.get(`${API}/family/addresses`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAddresses(res.data || []);
    } catch (err) {
      console.error(err);
      toast.error(getErrorMessage(err, 'Failed to load parent addresses'));
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAddress = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/family/addresses`, formData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("Parents' Home Address added!");
      setShowAddModal(false);
      setFormData({
        parent_name: '',
        parent_phone: '',
        address: '',
        city: 'Hyderabad',
        preferred_language: 'Telugu',
        landmark: ''
      });
      fetchAddresses();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to add parent address'));
    }
  };

  const handleDeleteAddress = async (id) => {
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API}/family/addresses/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Address removed');
      fetchAddresses();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to delete address'));
    }
  };

  const fetchTracking = async (jobId) => {
    if (!jobId) return;
    try {
      const token = localStorage.getItem('token');
      const res = await axios.get(`${API}/family/bookings/${jobId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTrackingData(res.data);
    } catch (err) {
      toast.error('Could not load parent tracking details');
    }
  };

  const handleVerifyOtp = async () => {
    if (!otpInput.trim() || !activeJobId) return;
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${API}/family/bookings/${activeJobId}/verify-otp`,
        { otp: otpInput },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('✓ Parent Arrival OTP Verified!');
      fetchTracking(activeJobId);
      setOtpInput('');
    } catch (err) {
      toast.error(getErrorMessage(err, 'Invalid OTP Code'));
    }
  };

  const handleNeedHelp = async () => {
    if (!activeJobId) return;
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${API}/family/bookings/${activeJobId}/support`,
        { message: 'Parent requested immediate telephone or agent support.' },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('🚨 Support Alert Sent! A Sanyuth agent will contact your parent shortly.');
    } catch (err) {
      toast.error('Failed to submit support request');
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      {/* Family / Address Banner */}
      <div className="bg-gradient-to-r from-orange-600 to-amber-600 p-6 rounded-2xl text-white shadow-xl flex flex-wrap justify-between items-center gap-4">
        <div className="flex items-center space-x-3">
          <div className="p-3 bg-white/20 rounded-xl backdrop-blur-md">
            <MapPin className="w-7 h-7 text-white" />
          </div>
          <div>
            <span className="text-xs uppercase font-bold tracking-wider text-orange-100">Saved Locations</span>
            <h1 className="text-2xl font-bold">Add & Manage Addresses</h1>
            <p className="text-xs text-orange-100 mt-0.5">Save parent, family, or home addresses for quick and convenient service bookings</p>
          </div>
        </div>

        <button
          onClick={() => setShowAddModal(true)}
          className="px-4 py-2.5 bg-white text-orange-700 hover:bg-orange-50 rounded-xl font-bold text-sm shadow-sm transition flex items-center"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add New Address
        </button>
      </div>

      {/* Tabs */}
      <div className="flex space-x-3 border-b border-gray-200">
        <button
          onClick={() => setActiveTab('addresses')}
          className={`pb-3 text-sm font-bold border-b-2 transition ${
            activeTab === 'addresses' ? 'border-orange-600 text-orange-600' : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Saved Addresses ({addresses.length})
        </button>
        <button
          onClick={() => setActiveTab('live_tracking')}
          className={`pb-3 text-sm font-bold border-b-2 transition ${
            activeTab === 'live_tracking' ? 'border-orange-600 text-orange-600' : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
        >
          Active Address Bookings & Status
        </button>
      </div>

      {/* Saved Addresses Tab */}
      {activeTab === 'addresses' && (
        <div className="space-y-4">
          {loading ? (
            <div className="p-6 bg-white rounded-xl shadow-sm border border-gray-100 animate-pulse"></div>
          ) : addresses.length === 0 ? (
            <div className="p-8 text-center bg-gray-50 border border-dashed border-gray-300 rounded-2xl space-y-3">
              <MapPin className="w-10 h-10 text-orange-400 mx-auto" />
              <p className="text-sm font-semibold text-gray-700">No Saved Addresses Yet</p>
              <p className="text-xs text-gray-400 max-w-md mx-auto">Add parent or family home addresses to quickly select them when posting a job or booking home services.</p>
              <button
                onClick={() => setShowAddModal(true)}
                className="px-4 py-2 bg-orange-600 text-white rounded-lg text-xs font-bold shadow hover:bg-orange-700"
              >
                Add New Address
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {addresses.map((addr) => (
                <div key={addr.id} className="bg-white p-5 rounded-2xl border border-gray-200 shadow-sm hover:border-rose-300 transition space-y-3">
                  <div className="flex justify-between items-start">
                    <div>
                      <span className="text-xs font-bold text-rose-600 uppercase tracking-wider">{addr.city} • {addr.preferred_language}</span>
                      <h3 className="text-lg font-bold text-gray-900 flex items-center mt-0.5">
                        <User className="w-4 h-4 mr-1.5 text-gray-500" />
                        {addr.parent_name}
                      </h3>
                    </div>
                    <button
                      onClick={() => handleDeleteAddress(addr.id)}
                      className="text-gray-400 hover:text-rose-600 p-1 rounded"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>

                  <div className="space-y-1 text-xs text-gray-600">
                    <div className="flex items-center"><Phone className="w-3.5 h-3.5 mr-1.5 text-gray-400" />{addr.parent_phone}</div>
                    <div className="flex items-start"><MapPin className="w-3.5 h-3.5 mr-1.5 text-rose-500 mt-0.5 shrink-0" />{addr.address}</div>
                  </div>

                  {onSelectAddressForBooking && (
                    <button
                      onClick={() => onSelectAddressForBooking(addr)}
                      className="w-full py-2 bg-rose-50 hover:bg-rose-100 text-rose-700 rounded-lg text-xs font-bold transition"
                    >
                      Book Service for This Address
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Live Tracking Tab */}
      {activeTab === 'live_tracking' && (
        <div className="space-y-6">
          <div className="bg-white p-4 rounded-xl border border-gray-200 flex items-center space-x-3">
            <input
              type="text"
              placeholder="Enter Job ID to track (e.g. demo job ID)"
              value={activeJobId}
              onChange={(e) => setActiveJobId(e.target.value)}
              className="flex-1 text-sm border border-gray-300 rounded-lg p-2.5 focus:outline-none"
            />
            <button
              onClick={() => fetchTracking(activeJobId)}
              className="px-4 py-2.5 bg-rose-600 text-white rounded-lg text-sm font-bold hover:bg-rose-700"
            >
              Track Booking
            </button>
          </div>

          {trackingData && (
            <div className="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm space-y-6">
              {/* Status Header */}
              <div className="flex justify-between items-center border-b pb-4">
                <div>
                  <span className="text-xs font-bold text-gray-400 uppercase">Parent Booking Status</span>
                  <h3 className="text-xl font-bold text-gray-900">{trackingData.title}</h3>
                  <p className="text-xs text-gray-500">For: {trackingData.parent_name} ({trackingData.parent_phone})</p>
                </div>
                <span className="px-3 py-1 bg-emerald-100 text-emerald-800 rounded-full text-xs font-extrabold uppercase">
                  {trackingData.arrival_status}
                </span>
              </div>

              {/* Arrival Verification OTP Box */}
              <div className="bg-amber-50 border border-amber-200 p-4 rounded-xl space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-xs font-bold text-amber-900 flex items-center">
                    <KeyRound className="w-4 h-4 mr-1 text-amber-600" />
                    Parent Arrival Verification OTP
                  </span>
                  <span className="text-lg font-mono font-bold text-amber-900 tracking-widest px-2 py-0.5 bg-white rounded border border-amber-300">
                    {trackingData.otp}
                  </span>
                </div>
                <p className="text-xs text-amber-800">
                  Give this 4-digit OTP code to the service worker when they arrive at your parents' doorstep to verify identity and start work safely.
                </p>

                {/* Worker OTP Entry Test */}
                <div className="flex items-center space-x-2 pt-2">
                  <input
                    type="text"
                    placeholder="Worker enter 4-digit OTP"
                    value={otpInput}
                    onChange={(e) => setOtpInput(e.target.value)}
                    className="text-xs border border-amber-300 rounded p-1.5 w-40 focus:outline-none"
                  />
                  <button
                    onClick={handleVerifyOtp}
                    className="px-3 py-1.5 bg-amber-600 text-white rounded text-xs font-bold hover:bg-amber-700"
                  >
                    Verify OTP
                  </button>
                </div>
              </div>

              {/* Assigned Worker Info */}
              {trackingData.worker && (
                <div className="flex items-center space-x-4 p-4 bg-gray-50 rounded-xl">
                  <div className="w-12 h-12 rounded-full bg-rose-100 text-rose-600 font-bold flex items-center justify-center text-lg">
                    {trackingData.worker.name[0]}
                  </div>
                  <div>
                    <h4 className="font-bold text-gray-900">{trackingData.worker.name}</h4>
                    <p className="text-xs text-gray-500">Phone: {trackingData.worker.phone} • Rating: ⭐ {trackingData.worker.rating_avg}</p>
                  </div>
                </div>
              )}

              {/* Support Button */}
              <div className="flex justify-end pt-2">
                <button
                  onClick={handleNeedHelp}
                  className="px-4 py-2 bg-rose-100 text-rose-700 hover:bg-rose-200 rounded-lg text-xs font-bold flex items-center"
                >
                  <HelpCircle className="w-4 h-4 mr-1.5" />
                  Need Help? (Contact Sanyuth Support)
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Modal to Add Parent Address */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-6 max-w-md w-full shadow-2xl">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Add Parents' Home Address</h3>
            <form onSubmit={handleCreateAddress} className="space-y-3">
              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Parent's Full Name</label>
                <input
                  type="text"
                  required
                  value={formData.parent_name}
                  onChange={(e) => setFormData({ ...formData, parent_name: e.target.value })}
                  placeholder="e.g. Ramesh Kumar (Father)"
                  className="w-full text-sm border border-gray-300 rounded-lg p-2.5 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Parent's Phone Number</label>
                <input
                  type="tel"
                  required
                  value={formData.parent_phone}
                  onChange={(e) => setFormData({ ...formData, parent_phone: e.target.value })}
                  placeholder="e.g. 9876500001"
                  className="w-full text-sm border border-gray-300 rounded-lg p-2.5 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Full House Address</label>
                <textarea
                  required
                  rows={2}
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  placeholder="House No, Street, Colony..."
                  className="w-full text-sm border border-gray-300 rounded-lg p-2.5 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-1">City</label>
                  <input
                    type="text"
                    required
                    value={formData.city}
                    onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                    className="w-full text-sm border border-gray-300 rounded-lg p-2.5 focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-gray-700 mb-1">Preferred Language</label>
                  <select
                    value={formData.preferred_language}
                    onChange={(e) => setFormData({ ...formData, preferred_language: e.target.value })}
                    className="w-full text-sm border border-gray-300 rounded-lg p-2.5 focus:outline-none bg-white"
                  >
                    <option value="Telugu">Telugu</option>
                    <option value="Hindi">Hindi</option>
                    <option value="English">English</option>
                  </select>
                </div>
              </div>

              <div className="flex justify-end space-x-3 pt-3">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 text-sm font-semibold text-gray-600 hover:bg-gray-100 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-sm font-bold text-white bg-rose-600 hover:bg-rose-700 rounded-lg shadow-sm"
                >
                  Save Address
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

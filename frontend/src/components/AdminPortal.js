import React, { useState, useEffect } from 'react';
import { 
  Users, 
  Briefcase, 
  IndianRupee, 
  AlertTriangle, 
  TrendingUp, 
  Shield, 
  Settings, 
  Bell,
  Eye,
  CheckCircle,
  XCircle,
  Flag,
  FileText,
  BarChart3,
  UserCheck,
  MessageSquare,
  Activity,
  Calendar,
  Search,
  Filter,
  Download,
  Plus,
  Edit,
  Trash2,
  AlertCircle,
  Clock,
  Star,
  Phone,
  Mail,
  MapPin,
  DollarSign,
  Target
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';
import { API, getErrorMessage } from '../lib/api';

// Main Admin Dashboard Component
export const AdminDashboard = () => {
  const [dashboardStats, setDashboardStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardStats();
  }, []);

  const fetchDashboardStats = async () => {
    try {
      const response = await axios.get(`${API}/admin/dashboard`);
      setDashboardStats(response.data);
    } catch (error) {
      toast.error('Failed to fetch dashboard data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <AdminDashboardSkeleton />;
  }

  return (
    <div className="p-6 space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
          <p className="text-gray-600">Complete platform oversight and management</p>
        </div>
        <div className="flex items-center space-x-4">
          <button className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700">
            <Plus className="w-4 h-4 mr-2 inline" />
            New Announcement
          </button>
        </div>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Users"
          value={dashboardStats?.total_users || 0}
          icon={Users}
          color="blue"
          subtext={`${dashboardStats?.total_customers || 0} customers, ${dashboardStats?.total_workers || 0} workers`}
        />
        <MetricCard
          title="Active Jobs"
          value={dashboardStats?.active_jobs || 0}
          icon={Briefcase}
          color="green"
          subtext={`${dashboardStats?.completed_jobs || 0} completed`}
        />
        <MetricCard
          title="Monthly Revenue"
          value={`₹${(dashboardStats?.total_revenue_month || 0).toLocaleString()}`}
          icon={IndianRupee}
          color="orange"
          subtext={`₹${(dashboardStats?.total_revenue_today || 0).toLocaleString()} today`}
        />
        <MetricCard
          title="Pending Issues"
          value={(dashboardStats?.pending_disputes || 0) + (dashboardStats?.pending_kyc || 0)}
          icon={AlertTriangle}
          color="red"
          subtext={`${dashboardStats?.pending_disputes || 0} disputes, ${dashboardStats?.pending_kyc || 0} KYC`}
        />
      </div>

      {/* Charts and Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Revenue Chart */}
        <div className="lg:col-span-2 bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold mb-4">Revenue Overview</h3>
          <div className="flex h-64 items-end pb-8 gap-4 px-4 overflow-x-auto border-b border-l">
            {/* CSS Bar Chart Simulation */}
            {[45, 60, 30, 80, 50, 95, 75].map((val, idx) => (
              <div key={idx} className="flex flex-col items-center flex-1 group">
                <div 
                  className="w-full bg-orange-500 hover:bg-orange-600 rounded-t-sm transition-all duration-300 relative"
                  style={{ height: `${val}%` }}
                >
                  <span className="absolute -top-6 left-1/2 -translate-x-1/2 text-xs font-bold text-gray-600 opacity-0 group-hover:opacity-100 transition-opacity">
                    ₹{val * 1000}
                  </span>
                </div>
                <span className="text-xs text-gray-500 mt-2">Day {idx + 1}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Activities */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold mb-4">Recent Activities</h3>
          <div className="space-y-4">
            {dashboardStats?.recent_activities?.map((activity, index) => (
              <div key={index} className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
                <div className="flex-1">
                  <p className="text-sm text-gray-900">{activity.description}</p>
                  <p className="text-xs text-gray-500">{activity.time}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Top Performing Workers */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="text-lg font-semibold mb-4">Top Performing Workers</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="text-left py-2">Name</th>
                <th className="text-left py-2">Rating</th>
                <th className="text-left py-2">Reviews</th>
                <th className="text-left py-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {dashboardStats?.top_performing_workers?.map((worker, index) => (
                <tr key={index} className="border-b">
                  <td className="py-2">{worker.name}</td>
                  <td className="py-2">
                    <div className="flex items-center">
                      <Star className="w-4 h-4 text-yellow-400 mr-1" />
                      {worker.rating_avg}
                    </div>
                  </td>
                  <td className="py-2">{worker.reviews_count}</td>
                  <td className="py-2">
                    <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs">
                      Active
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// Metric Card Component
const MetricCard = ({ title, value, icon: Icon, color, subtext }) => {
  const colorClasses = {
    blue: 'bg-blue-100 text-blue-600',
    green: 'bg-green-100 text-green-600',
    orange: 'bg-orange-100 text-orange-600',
    red: 'bg-red-100 text-red-600'
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
          {subtext && <p className="text-xs text-gray-500 mt-1">{subtext}</p>}
        </div>
        <div className={`p-3 rounded-lg ${colorClasses[color]}`}>
          <Icon className="w-6 h-6" />
        </div>
      </div>
    </div>
  );
};

// User Management Component
export const AdminUserManagement = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    role: '',
    search: '',
    status: ''
  });
  const [selectedUser, setSelectedUser] = useState(null);
  const [showStrikeModal, setShowStrikeModal] = useState(false);
  const [strikeDesc, setStrikeDesc] = useState('');
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [userActivity, setUserActivity] = useState(null);

  useEffect(() => {
    fetchUsers();
  }, [filters]);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filters.role) params.append('role', filters.role);
      if (filters.search) params.append('search', filters.search);
      if (filters.status) params.append('status', filters.status);

      const response = await axios.get(`${API}/admin/users?${params.toString()}`);
      setUsers(response.data);
    } catch (error) {
      toast.error('Failed to fetch users');
    } finally {
      setLoading(false);
    }
  };

  const handleUserAction = async (userId, action, data = {}) => {
    try {
      let response;
      switch (action) {
        case 'suspend':
          response = await axios.put(`${API}/admin/users/${userId}/suspend`, data);
          break;
        case 'strike':
          response = await axios.post(`${API}/admin/users/${userId}/strike`, data);
          break;
        case 'verify':
          response = await axios.put(`${API}/admin/users/${userId}/verify`, data);
          break;
        default:
          return;
      }
      toast.success(response.data?.message || 'Action completed');
      if (action === 'strike' && response.data?.suspended) {
        toast.warning('This user reached the strike limit and has been suspended');
      }
      fetchUsers();
    } catch (error) {
      toast.error(getErrorMessage(error, 'Action failed'));
    }
  };

  const openUserDetails = async (user) => {
    setSelectedUser(user);
    setUserActivity(null);
    setShowDetailsModal(true);
    try {
      const response = await axios.get(`${API}/admin/users/${user.id}/activity`);
      setUserActivity(response.data);
    } catch (error) {
      toast.error(getErrorMessage(error, 'Failed to load user activity'));
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">User Management</h1>
          <p className="text-gray-600">Manage customer and worker accounts</p>
        </div>
        <div className="flex items-center space-x-4">
          <button className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50">
            <Download className="w-4 h-4 mr-2 inline" />
            Export Users
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Search Users</label>
            <div className="relative">
              <Search className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
              <input
                type="text"
                value={filters.search}
                onChange={(e) => setFilters({...filters, search: e.target.value})}
                placeholder="Name, phone, or email..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-orange-500 focus:border-orange-500"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Role</label>
            <select
              value={filters.role}
              onChange={(e) => setFilters({...filters, role: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-orange-500 focus:border-orange-500"
            >
              <option value="">All Roles</option>
              <option value="customer">Customers</option>
              <option value="worker">Workers</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
            <select
              value={filters.status}
              onChange={(e) => setFilters({...filters, status: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-orange-500 focus:border-orange-500"
            >
              <option value="">All Status</option>
              <option value="active">Active</option>
              <option value="suspended">Suspended</option>
              <option value="pending_verification">Pending Verification</option>
            </select>
          </div>
          <div className="flex items-end">
            <button
              onClick={() => setFilters({ role: '', search: '', status: '' })}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
            >
              Clear Filters
            </button>
          </div>
        </div>
      </div>

      {/* Users Table */}
      <div className="bg-white rounded-lg shadow-sm border">
        <div className="px-6 py-4 border-b">
          <h3 className="text-lg font-semibold">User Accounts ({users.length})</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">User</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Role</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Rating</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Joined</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {users.map((user) => (
                <tr key={user.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="flex items-center">
                      <div className="w-10 h-10 bg-orange-100 rounded-full flex items-center justify-center">
                        <span className="text-orange-600 font-medium">
                          {user.name?.charAt(0) || '?'}
                        </span>
                      </div>
                      <div className="ml-4">
                        <div className="font-medium text-gray-900">{user.name}</div>
                        <div className="text-sm text-gray-500">{user.phone}</div>
                        {user.email && <div className="text-sm text-gray-500">{user.email}</div>}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      user.role === 'customer' ? 'bg-blue-100 text-blue-800' : 'bg-green-100 text-green-800'
                    }`}>
                      {user.role}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex flex-col gap-1 items-start">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        user.status === 'suspended' ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
                      }`}>
                        {user.status === 'suspended' ? 'Suspended' : 'Active'}
                      </span>
                      {user.kyc_verified && (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                          Verified
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center">
                      <Star className="w-4 h-4 text-yellow-400 mr-1" />
                      <span>{user.rating_avg?.toFixed(1) || 'N/A'}</span>
                      <span className="text-gray-500 ml-1">({user.reviews_count || 0})</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {new Date(user.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => openUserDetails(user)}
                        className="text-blue-600 hover:text-blue-700"
                        title="View Details"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      {user.role !== 'admin' && (
                        <>
                          <button
                            onClick={() => handleUserAction(user.id, 'verify', { verified: !user.kyc_verified })}
                            className={user.kyc_verified ? 'text-gray-400 hover:text-gray-600' : 'text-green-600 hover:text-green-700'}
                            title={user.kyc_verified ? 'Remove Verification' : 'Verify User'}
                          >
                            <UserCheck className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => {
                              const suspend = user.status !== 'suspended';
                              if (suspend && !window.confirm(`Suspend ${user.name}? They will be logged out and unable to sign in.`)) {
                                return;
                              }
                              handleUserAction(user.id, 'suspend', { suspend });
                            }}
                            className={user.status === 'suspended' ? 'text-green-600 hover:text-green-700' : 'text-orange-600 hover:text-orange-700'}
                            title={user.status === 'suspended' ? 'Reactivate User' : 'Suspend User'}
                          >
                            {user.status === 'suspended' ? <CheckCircle className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
                          </button>
                        </>
                      )}
                      <button 
                        onClick={() => { setSelectedUser(user); setShowStrikeModal(true); }}
                        className="text-red-600 hover:text-red-700"
                        title="Issue Strike"
                      >
                        <AlertTriangle className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {showStrikeModal && selectedUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h3 className="text-xl font-bold mb-4">Issue Strike to {selectedUser.name}</h3>
            <p className="text-sm text-gray-600 mb-4">A user is automatically suspended upon reaching 3 strikes.</p>
            <textarea
              className="w-full p-2 border rounded-lg mb-4"
              rows="3"
              placeholder="Reason for strike..."
              value={strikeDesc}
              onChange={(e) => setStrikeDesc(e.target.value)}
            ></textarea>
            <div className="flex justify-end space-x-2">
              <button onClick={() => setShowStrikeModal(false)} className="px-4 py-2 border rounded-lg">Cancel</button>
              <button 
                onClick={() => {
                  handleUserAction(selectedUser.id, 'strike', { reason: 'policy_violation', description: strikeDesc });
                  setShowStrikeModal(false);
                  setStrikeDesc('');
                }} 
                disabled={!strikeDesc.trim()}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
              >
                Confirm Strike
              </button>
            </div>
          </div>
        </div>
      )}

      {showDetailsModal && selectedUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-xl font-bold">{selectedUser.name}</h3>
                <p className="text-sm text-gray-500 capitalize">{selectedUser.role} · {selectedUser.phone}</p>
              </div>
              <button onClick={() => setShowDetailsModal(false)} className="text-gray-400 hover:text-gray-600">
                <XCircle className="w-5 h-5" />
              </button>
            </div>
            {userActivity ? (
              <div className="grid grid-cols-2 gap-3 text-sm">
                {[
                  ['Status', userActivity.user?.status === 'suspended' ? 'Suspended' : 'Active'],
                  ['Active strikes', userActivity.active_strikes],
                  ['Jobs posted', userActivity.jobs_posted],
                  ['Applications', userActivity.applications_sent],
                  ['Bids placed', userActivity.bids_placed],
                  ['Payments made', userActivity.payments_made],
                  ['Payments received', userActivity.payments_received],
                  ['Reviews received', userActivity.reviews_received]
                ].map(([label, value]) => (
                  <div key={label} className="bg-gray-50 rounded-lg p-3">
                    <p className="text-gray-500 text-xs">{label}</p>
                    <p className="font-semibold text-gray-900">{value}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-8 text-center text-gray-500">Loading activity...</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// Dispute Management Component
export const AdminDisputeManagement = () => {
  const [disputes, setDisputes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDispute, setSelectedDispute] = useState(null);

  useEffect(() => {
    fetchDisputes();
  }, []);

  const fetchDisputes = async () => {
    try {
      const response = await axios.get(`${API}/admin/disputes`);
      setDisputes(response.data);
    } catch (error) {
      toast.error('Failed to fetch disputes');
    } finally {
      setLoading(false);
    }
  };

  const handleDisputeAction = async (disputeId, actionType, details = {}) => {
    try {
      await axios.post(`${API}/admin/disputes/${disputeId}/action`, {
        action_type: actionType,
        details,
        notes: details.notes || ''
      });
      toast.success('Action completed successfully');
      fetchDisputes();
    } catch (error) {
      toast.error('Failed to process action');
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dispute Management</h1>
          <p className="text-gray-600">Resolve customer and worker disputes</p>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-500">
            {disputes.filter(d => d.status === 'open').length} Open Disputes
          </span>
        </div>
      </div>

      {/* Dispute Queue */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Open Disputes */}
        <div className="bg-white rounded-lg shadow-sm border">
          <div className="px-4 py-3 border-b bg-red-50">
            <h3 className="font-medium text-red-800">Open ({disputes.filter(d => d.status === 'open').length})</h3>
          </div>
          <div className="p-4 space-y-3 max-h-96 overflow-y-auto">
            {disputes.filter(d => d.status === 'open').map((dispute) => (
              <DisputeCard
                key={dispute.id}
                dispute={dispute}
                onSelect={() => setSelectedDispute(dispute)}
                onAction={handleDisputeAction}
              />
            ))}
          </div>
        </div>

        {/* Under Review */}
        <div className="bg-white rounded-lg shadow-sm border">
          <div className="px-4 py-3 border-b bg-yellow-50">
            <h3 className="font-medium text-yellow-800">Under Review ({disputes.filter(d => d.status === 'under_review').length})</h3>
          </div>
          <div className="p-4 space-y-3 max-h-96 overflow-y-auto">
            {disputes.filter(d => d.status === 'under_review').map((dispute) => (
              <DisputeCard
                key={dispute.id}
                dispute={dispute}
                onSelect={() => setSelectedDispute(dispute)}
                onAction={handleDisputeAction}
              />
            ))}
          </div>
        </div>

        {/* Resolved */}
        <div className="bg-white rounded-lg shadow-sm border">
          <div className="px-4 py-3 border-b bg-green-50">
            <h3 className="font-medium text-green-800">Resolved ({disputes.filter(d => d.status === 'resolved').length})</h3>
          </div>
          <div className="p-4 space-y-3 max-h-96 overflow-y-auto">
            {disputes.filter(d => d.status === 'resolved').map((dispute) => (
              <DisputeCard
                key={dispute.id}
                dispute={dispute}
                onSelect={() => setSelectedDispute(dispute)}
                onAction={handleDisputeAction}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

// Dispute Card Component
const DisputeCard = ({ dispute, onSelect, onAction }) => {
  const severityColors = {
    low: 'bg-blue-100 text-blue-800',
    medium: 'bg-yellow-100 text-yellow-800',
    high: 'bg-red-100 text-red-800',
    critical: 'bg-purple-100 text-purple-800'
  };

  return (
    <div
      className="p-3 border rounded-lg cursor-pointer hover:bg-gray-50"
      onClick={onSelect}
    >
      <div className="flex items-start justify-between mb-2">
        <h4 className="font-medium text-sm">{dispute.title}</h4>
        <span className={`px-2 py-1 rounded-full text-xs ${severityColors[dispute.severity]}`}>
          {dispute.severity}
        </span>
      </div>
      <p className="text-xs text-gray-600 mb-2 line-clamp-2">{dispute.description}</p>
      <div className="flex items-center justify-between text-xs text-gray-500">
        <span>{dispute.category}</span>
        <span>{new Date(dispute.created_at).toLocaleDateString()}</span>
      </div>
    </div>
  );
};

// Analytics Component
export const AdminAnalytics = () => {
  const [analytics, setAnalytics] = useState({
    revenue: null,
    jobs: null,
    users: null
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      const [revenueRes, jobsRes] = await Promise.all([
        axios.get(`${API}/admin/analytics/revenue?period=month`),
        axios.get(`${API}/admin/analytics/jobs`)
      ]);

      setAnalytics({
        revenue: revenueRes.data,
        jobs: jobsRes.data,
        users: { total_users: 150, growth_rate: 12.5 } // Mock data
      });
    } catch (error) {
      toast.error('Failed to fetch analytics');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="p-6"><div className="animate-pulse">Loading analytics...</div></div>;
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Platform Analytics</h1>
        <p className="text-gray-600">Insights and performance metrics</p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold mb-4">Revenue Analytics</h3>
          <div className="space-y-2">
            <div className="text-3xl font-bold text-green-600">
              ₹{analytics.revenue?.total_revenue?.toLocaleString() || 0}
            </div>
            <div className="text-sm text-gray-600">
              {analytics.revenue?.total_transactions || 0} transactions
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold mb-4">Job Performance</h3>
          <div className="space-y-2">
            <div className="text-3xl font-bold text-blue-600">
              {analytics.jobs?.completion_rate || 0}%
            </div>
            <div className="text-sm text-gray-600">
              {analytics.jobs?.completed_jobs || 0} / {analytics.jobs?.total_jobs || 0} jobs completed
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-lg font-semibold mb-4">User Growth</h3>
          <div className="space-y-2">
            <div className="text-3xl font-bold text-purple-600">
              {analytics.users?.growth_rate || 0}%
            </div>
            <div className="text-sm text-gray-600">
              Monthly growth rate
            </div>
          </div>
        </div>
      </div>

      {/* Category Performance */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="text-lg font-semibold mb-4">Job Category Performance</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="text-left py-2">Category</th>
                <th className="text-left py-2">Job Count</th>
                <th className="text-left py-2">Avg Amount</th>
                <th className="text-left py-2">Performance</th>
              </tr>
            </thead>
            <tbody>
              {analytics.jobs?.category_stats?.map((category, index) => (
                <tr key={index} className="border-b">
                  <td className="py-2 capitalize">{category._id}</td>
                  <td className="py-2">{category.job_count}</td>
                  <td className="py-2">₹{Math.round(category.avg_amount).toLocaleString()}</td>
                  <td className="py-2">
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-orange-600 h-2 rounded-full" 
                        style={{ width: `${(category.job_count / analytics.jobs.total_jobs) * 100}%` }}
                      ></div>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// Dashboard Skeleton
const AdminDashboardSkeleton = () => (
  <div className="p-6 space-y-8 animate-pulse">
    <div className="h-8 bg-gray-200 rounded w-1/4"></div>
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className="h-24 bg-gray-200 rounded-lg"></div>
      ))}
    </div>
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2 h-64 bg-gray-200 rounded-lg"></div>
      <div className="h-64 bg-gray-200 rounded-lg"></div>
    </div>
  </div>
);
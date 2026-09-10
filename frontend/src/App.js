import React, { useState, useEffect, useRef } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useParams } from 'react-router-dom';
import { AdminLogin } from './components/AdminLogin';
import { 
  AdminDashboard as AdminDashboardComponent, 
  AdminUserManagement as AdminUserManagementComponent, 
  AdminDisputeManagement as AdminDisputeManagementComponent, 
  AdminAnalytics as AdminAnalyticsComponent 
} from './components/AdminPortal';
import axios from 'axios';
import { Toaster } from './components/ui/sonner';
import { MessagingHub } from './components/MessagingHub';
import { toast } from 'sonner';

// Import Admin Portal Components
import { AdminDashboard, AdminUserManagement, AdminDisputeManagement, AdminAnalytics } from './components/AdminPortal';

// Import Lucide icons
import { 
  User, 
  Briefcase, 
  MapPin, 
  Clock, 
  Star, 
  Phone, 
  Mail,
  IndianRupee,
  Search,
  Filter,
  Plus,
  Bell,
  Menu,
  X,
  UserCircle,
  LogOut,
  Settings,
  Home,
  Users,
  Calendar,
  MessageCircle,
  CheckCircle,
  ArrowLeft,
  Camera,
  Upload,
  ChevronDown,
  Zap,
  Target,
  DollarSign,
  Clock3,
  Send,
  Eye,
  ThumbsUp,
  Award,
  TrendingUp,
  Filter as FilterIcon,
  SortAsc,
  MapPinIcon,
  Building,
  Wrench,
  HardHat,
  Hammer,
  Edit,
  Save,
  UserCheck,
  Handshake,
  FileText,
  ExternalLink,
  ChevronRight,
  AlertCircle,
  CheckCircle2,
  XCircle,
  Timer,
  BadgeCheck,
  Loader2
} from 'lucide-react';

import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = React.createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      // Set axios default header
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      // Fetch user info
      fetchUserInfo();
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchUserInfo = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      setUser(response.data);
    } catch (error) {
      console.error('Failed to fetch user info:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = (tokenData) => {
    setToken(tokenData.access_token);
    setUser(tokenData.user);
    localStorage.setItem('token', tokenData.access_token);
    axios.defaults.headers.common['Authorization'] = `Bearer ${tokenData.access_token}`;
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Components
const Header = ({ onMenuClick }) => {
  const { user, logout } = useAuth();
  const [showProfile, setShowProfile] = useState(false);

  return (
    <header className="bg-white shadow-sm border-b border-orange-100 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <button
              onClick={onMenuClick}
              className="p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100 lg:hidden"
            >
              <Menu className="w-6 h-6" />
            </button>
            <div className="flex-shrink-0 ml-2 lg:ml-0">
              <h1 className="text-2xl font-bold text-orange-600">Sanyuth</h1>
              <p className="text-xs text-gray-500">AI Powered - Blue Collar Marketplace</p>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <button className="p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100">
              <Bell className="w-5 h-5" />
            </button>
            
            <div className="relative">
              <button
                onClick={() => setShowProfile(!showProfile)}
                className="flex items-center space-x-2 p-2 rounded-md hover:bg-gray-100"
              >
                <UserCircle className="w-6 h-6 text-gray-600" />
                <span className="text-sm font-medium text-gray-700 hidden sm:block">
                  {user?.name}
                </span>
              </button>
              
              {showProfile && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-50 border">
                  <div className="px-4 py-2 border-b">
                    <p className="text-sm font-medium text-gray-900">{user?.name}</p>
                    <p className="text-xs text-gray-500 capitalize">{user?.role}</p>
                  </div>
                  <button className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                    <Settings className="w-4 h-4 mr-2" />
                    Settings
                  </button>
                  <button
                    onClick={logout}
                    className="flex items-center w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                  >
                    <LogOut className="w-4 h-4 mr-2" />
                    Logout
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

const Sidebar = ({ isOpen, onClose, activeRoute, setActiveRoute }) => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const menuItems = {
    customer: [
      { name: 'Dashboard', icon: Home, route: 'dashboard' },
      { name: 'My Jobs', icon: Briefcase, route: 'my-jobs' },
      { name: 'Post Job', icon: Plus, route: 'post-job' },
      { name: 'Messages', icon: MessageCircle, route: 'messages' }
    ],
    worker: [
      { name: 'Dashboard', icon: Home, route: 'dashboard' },
      { name: 'Find Jobs', icon: Search, route: 'find-jobs' },
      { name: 'My Applications', icon: Calendar, route: 'my-applications' },
      { name: 'Profile', icon: User, route: 'profile' },
      { name: 'Messages', icon: MessageCircle, route: 'messages' }
    ],
    admin: [
      { name: 'Dashboard', icon: Home, route: 'admin/dashboard' },
      { name: 'User Management', icon: Users, route: 'admin/users' },
      { name: 'Dispute Management', icon: Settings, route: 'admin/disputes' },
      { name: 'Analytics', icon: TrendingUp, route: 'admin/analytics' },
      { name: 'Jobs', icon: Briefcase, route: 'admin/jobs' }
    ]
  };

  const items = menuItems[user?.role] || [];

  const handleNavigation = (route) => {
    setActiveRoute(route);
    navigate(`/${route}`);
    onClose();
  };

  return (
    <>
      {/* Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}
      
      {/* Sidebar */}
      <div className={`
        fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out
        lg:translate-x-0 lg:static lg:inset-0
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="flex items-center justify-between h-16 px-6 border-b border-orange-100">
          <h2 className="text-lg font-semibold text-gray-900 capitalize">
            {user?.role} Panel
          </h2>
          <button
            onClick={onClose}
            className="p-1 rounded-md hover:bg-gray-100 lg:hidden"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <nav className="mt-6">
          <div className="px-3">
            {items.map((item, index) => (
              <button
                key={index}
                onClick={() => handleNavigation(item.route)}
                className={`flex items-center w-full px-3 py-2 mt-1 text-sm font-medium rounded-md transition-colors ${
                  activeRoute === item.route 
                    ? 'bg-orange-100 text-orange-700' 
                    : 'text-gray-700 hover:bg-orange-50 hover:text-orange-600'
                }`}
              >
                <item.icon className="w-5 h-5 mr-3" />
                {item.name}
              </button>
            ))}
          </div>
        </nav>
      </div>
    </>
  );
};

// Enhanced Worker Profile Component
const WorkerProfile = () => {
  const { user } = useAuth();
  const [profile, setProfile] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState({
    skills: [],
    experience_years: 0,
    certifications: [],
    preferred_locations: []
  });

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const response = await axios.get(`${API}/workers/profile`);
      setProfile(response.data);
      setFormData({
        skills: response.data.skills || [],
        experience_years: response.data.experience_years || 0,
        certifications: response.data.certifications || [],
        preferred_locations: response.data.preferred_locations || []
      });
    } catch (error) {
      toast.error('Failed to fetch profile');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      const response = await axios.put(`${API}/workers/profile`, formData);
      setProfile(response.data);
      setIsEditing(false);
      toast.success('Profile updated successfully!');
    } catch (error) {
      toast.error('Failed to update profile');
    }
  };

  const addSkill = (skill) => {
    if (skill && !formData.skills.includes(skill)) {
      setFormData(prev => ({
        ...prev,
        skills: [...prev.skills, skill]
      }));
    }
  };

  const removeSkill = (skillToRemove) => {
    setFormData(prev => ({
      ...prev,
      skills: prev.skills.filter(skill => skill !== skillToRemove)
    }));
  };

  if (loading) {
    return <div className="p-6"><div className="animate-pulse">Loading profile...</div></div>;
  }

  return (
    <div className="p-6">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
          <div className="flex justify-between items-start mb-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Worker Profile</h1>
              <p className="text-gray-600">Build your professional profile to attract more customers</p>
            </div>
            <button
              onClick={() => isEditing ? handleSave() : setIsEditing(true)}
              className="flex items-center px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700"
            >
              {isEditing ? <Save className="w-4 h-4 mr-2" /> : <Edit className="w-4 h-4 mr-2" />}
              {isEditing ? 'Save Changes' : 'Edit Profile'}
            </button>
          </div>

          {/* Basic Info */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Name</label>
                <input
                  type="text"
                  value={user?.name || ''}
                  disabled
                  className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Phone</label>
                <input
                  type="text"
                  value={user?.phone || ''}
                  disabled
                  className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
                />
              </div>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Experience (Years)</label>
                <input
                  type="number"
                  value={formData.experience_years}
                  onChange={(e) => setFormData(prev => ({ ...prev, experience_years: parseInt(e.target.value) || 0 }))}
                  disabled={!isEditing}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-orange-500 focus:border-orange-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Trust Score</label>
                <div className="flex items-center">
                  <div className="flex-1 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-green-600 h-2 rounded-full" 
                      style={{ width: `${profile?.trust_score || 50}%` }}
                    ></div>
                  </div>
                  <span className="ml-3 text-sm font-medium text-gray-700">{profile?.trust_score || 50}%</span>
                </div>
              </div>
            </div>
          </div>

          {/* Skills Section */}
          <div className="mb-8">
            <label className="block text-sm font-medium text-gray-700 mb-3">Skills</label>
            <div className="flex flex-wrap gap-2 mb-3">
              {formData.skills.map((skill, index) => (
                <span
                  key={index}
                  className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-orange-100 text-orange-800"
                >
                  {skill}
                  {isEditing && (
                    <button
                      onClick={() => removeSkill(skill)}
                      className="ml-2 text-orange-600 hover:text-orange-800"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  )}
                </span>
              ))}
            </div>
            {isEditing && (
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="Add a skill..."
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-orange-500 focus:border-orange-500"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      addSkill(e.target.value);
                      e.target.value = '';
                    }
                  }}
                />
                <button
                  onClick={(e) => {
                    const input = e.target.parentNode.querySelector('input');
                    addSkill(input.value);
                    input.value = '';
                  }}
                  className="px-4 py-2 bg-orange-600 text-white rounded-md hover:bg-orange-700"
                >
                  Add
                </button>
              </div>
            )}
          </div>

          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">{profile?.completed_jobs || 0}</div>
              <div className="text-sm text-gray-600">Jobs Completed</div>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-yellow-600">{user?.rating_avg || 0}</div>
              <div className="text-sm text-gray-600">Average Rating</div>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">{profile?.cancelled_jobs || 0}</div>
              <div className="text-sm text-gray-600">Cancelled Jobs</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Bidding Component for Contractual Jobs
const BiddingModal = ({ job, isOpen, onClose, onSuccess }) => {
  const [bidData, setBidData] = useState({
    bid_amount: job?.budget_amount || '',
    visiting_charge: 0,
    message: ''
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await axios.post(`${API}/jobs/${job.id}/bid`, bidData);
      toast.success('Bid submitted successfully!');
      onSuccess();
      onClose();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to submit bid');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-md w-full p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Place Your Bid</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="mb-4 p-4 bg-gray-50 rounded-lg">
          <h4 className="font-medium text-gray-900">{job?.title}</h4>
          <p className="text-sm text-gray-600 mt-1">Budget: ₹{job?.budget_amount?.toLocaleString()}</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Your Bid Amount *
            </label>
            <div className="relative">
              <IndianRupee className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
              <input
                type="number"
                required
                value={bidData.bid_amount}
                onChange={(e) => setBidData(prev => ({ ...prev, bid_amount: parseFloat(e.target.value) || '' }))}
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-orange-500 focus:border-orange-500"
                placeholder="Enter your bid amount"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Site Visiting Charge (Optional)
            </label>
            <div className="relative">
              <IndianRupee className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
              <input
                type="number"
                value={bidData.visiting_charge}
                onChange={(e) => setBidData(prev => ({ ...prev, visiting_charge: parseFloat(e.target.value) || 0 }))}
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-orange-500 focus:border-orange-500"
                placeholder="0"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Message to Customer
            </label>
            <textarea
              value={bidData.message}
              onChange={(e) => setBidData(prev => ({ ...prev, message: e.target.value }))}
              rows={3}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-orange-500 focus:border-orange-500"
              placeholder="Tell the customer why you're the right choice..."
            />
          </div>

          <div className="bg-orange-50 p-3 rounded-lg">
            <div className="flex justify-between text-sm">
              <span>Bid Amount:</span>
              <span>₹{bidData.bid_amount?.toLocaleString() || 0}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span>Visiting Charge:</span>
              <span>₹{bidData.visiting_charge?.toLocaleString() || 0}</span>
            </div>
            <div className="flex justify-between font-medium border-t pt-2 mt-2">
              <span>Total:</span>
              <span>₹{((bidData.bid_amount || 0) + (bidData.visiting_charge || 0)).toLocaleString()}</span>
            </div>
          </div>

          <div className="flex gap-3">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !bidData.bid_amount}
              className="flex-1 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:opacity-50"
            >
              {loading ? 'Submitting...' : 'Submit Bid'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Utility Component for Star Rating Display
const StarRating = ({ rating, count, size = "sm", interactive = false, onRate = null }) => {
  const [hovered, setHovered] = useState(0);
  
  return (
    <div className="flex items-center">
      <div className="flex items-center">
        {[1, 2, 3, 4, 5].map((star) => (
          <Star
            key={star}
            onClick={() => interactive && onRate && onRate(star)}
            onMouseEnter={() => interactive && setHovered(star)}
            onMouseLeave={() => interactive && setHovered(0)}
            className={`${size === 'sm' ? 'w-4 h-4' : 'w-5 h-5'} ${
              star <= (hovered || rating) 
                ? 'text-yellow-400 fill-current' 
                : 'text-gray-300'
            } ${interactive ? 'cursor-pointer hover:scale-110 transition-transform' : ''}`}
          />
        ))}
      </div>
      {count !== undefined && (
        <span className="ml-2 text-sm text-gray-500">({count})</span>
      )}
    </div>
  );
};

// Review Modal Component
const ReviewModal = ({ isOpen, onClose, onSubmit, workerName }) => {
  const [stars, setStars] = useState(0);
  const [comment, setComment] = useState('');
  const [submitting, setSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async () => {
    if (stars === 0) {
      toast.error('Please select a star rating');
      return;
    }
    setSubmitting(true);
    await onSubmit({ stars, comment });
    setSubmitting(false);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden">
        <div className="p-6 border-b border-gray-100 flex justify-between items-center">
          <h2 className="text-xl font-bold text-gray-900">Rate {workerName}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <XCircle className="w-6 h-6" />
          </button>
        </div>
        <div className="p-6 space-y-6">
          <div className="text-center">
            <p className="text-gray-600 mb-4">How was your experience with this worker?</p>
            <div className="flex justify-center">
              <StarRating 
                rating={stars} 
                size="lg" 
                interactive={true} 
                onRate={setStars} 
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Share more details (Optional)
            </label>
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="What did you like? Anything that could be improved?"
              rows={4}
              className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-transparent resize-none"
            />
          </div>
        </div>
        <div className="p-6 bg-gray-50 flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-3 border border-gray-200 text-gray-700 rounded-xl hover:bg-white transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={submitting}
            className="flex-1 px-4 py-3 bg-orange-600 text-white rounded-xl hover:bg-orange-700 transition-colors disabled:opacity-50"
          >
            {submitting ? 'Submitting...' : 'Submit Review'}
          </button>
        </div>
      </div>
    </div>
  );
};

// Job Details & Application Management
const JobDetails = () => {
  const { jobId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [job, setJob] = useState(null);
  const [applications, setApplications] = useState([]);
  const [bids, setBids] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTab, setSelectedTab] = useState('details');
  const [showReviewModal, setShowReviewModal] = useState(false);

  useEffect(() => {
    if (jobId) {
      fetchJobDetails();
    }
  }, [jobId]);

  const fetchJobDetails = async () => {
    try {
      setLoading(true);
      const jobRes = await axios.get(`${API}/jobs/${jobId}`);
      setJob(jobRes.data);
      
      if (jobRes.data.type === 'daily') {
        const appRes = await axios.get(`${API}/jobs/${jobId}/applications`);
        setApplications(appRes.data);
      } else {
        const bidRes = await axios.get(`${API}/jobs/${jobId}/bids`);
        setBids(bidRes.data);
      }
    } catch (error) {
      console.error(error);
      toast.error('Failed to load job details');
    } finally {
      setLoading(false);
    }
  };

  const handleAssignWorker = async (workerId) => {
    try {
      await axios.post(`${API}/jobs/${jobId}/assign`, null, {
        params: { worker_id: workerId }
      });
      toast.success('Worker assigned successfully!');
      fetchJobDetails();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Assignment failed');
    }
  };

  const handleSubmitReview = async (reviewData) => {
    try {
      let workerId = '';
      if (job.type === 'daily') {
        const acceptedApp = applications.find(a => a.status === 'accepted');
        workerId = acceptedApp?.worker_id;
      } else {
        const acceptedBid = bids.find(b => b.status === 'accepted');
        workerId = acceptedBid?.worker_id;
      }

      await axios.post(`${API}/jobs/${jobId}/review`, {
        stars: reviewData.stars,
        comment: reviewData.comment,
        job_id: jobId,
        reviewee_user_id: workerId
      });
      toast.success('Review submitted! Thank you for your feedback.');
      fetchJobDetails();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to submit review');
    }
  };

  if (loading) return (
    <div className="p-8 flex justify-center">
      <Loader2 className="w-12 h-12 text-orange-500 animate-spin" />
    </div>
  );

  if (!job) return (
    <div className="p-8 text-center text-gray-500">
      <p>Job not found</p>
      <button onClick={() => navigate('/my-jobs')} className="mt-4 text-orange-600">Go Back</button>
    </div>
  );

  const isCustomer = user?.role === 'customer' && user?.id === job.customer_id;
  const isAssignedWorker = user?.role === 'worker' && (
    applications.some(a => a.worker_id === user.id && a.status === 'accepted') ||
    bids.some(b => b.worker_id === user.id && b.status === 'accepted')
  );

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        {/* Header Section */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden mb-6">
          <div className="p-6 sm:p-8 flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
            <div className="flex-1">
              <div className="flex flex-wrap items-center gap-3 mb-3">
                <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold ${
                  job.type === 'daily' ? 'bg-indigo-50 text-indigo-700' : 'bg-fuchsia-50 text-fuchsia-700'
                }`}>
                  {job.type === 'daily' ? <Zap className="w-3.5 h-3.5 mr-1" /> : <Target className="w-3.5 h-3.5 mr-1" />}
                  {job.type === 'daily' ? 'Daily Wage' : 'Contractual'}
                </span>
                <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold ${
                  job.status === 'open' ? 'bg-emerald-50 text-emerald-700' :
                  job.status === 'assigned' ? 'bg-blue-50 text-blue-700' :
                  job.status === 'completed' ? 'bg-gray-100 text-gray-700' :
                  'bg-amber-50 text-amber-700'
                }`}>
                  {job.status.charAt(0).toUpperCase() + job.status.slice(1)}
                </span>
              </div>
              <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">{job.title}</h1>
              <div className="flex flex-wrap items-center gap-4 text-sm text-gray-500">
                <span className="flex items-center"><MapPin className="w-4 h-4 mr-1" /> {job.location.address}</span>
                <span className="flex items-center"><Clock className="w-4 h-4 mr-1" /> {job.preferred_time_window?.start} - {job.preferred_time_window?.end}</span>
              </div>
            </div>
            <div className="text-left md:text-right">
              <p className="text-3xl font-extrabold text-orange-600">₹{job.budget_amount.toLocaleString()}</p>
              {job.is_budget_negotiable && <p className="text-sm font-medium text-emerald-600">Budget Negotiable</p>}
            </div>
          </div>
          
          {/* Action Footer for Customer */}
          {isCustomer && job.status === 'completed' && (
            <div className="px-6 py-4 bg-orange-50 border-t border-orange-100 flex items-center justify-between">
              <p className="text-sm text-orange-800 font-medium">Job has been completed and payment settled.</p>
              <button
                onClick={() => setShowReviewModal(true)}
                className="flex items-center px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 shadow-sm transition-all"
              >
                <Star className="w-4 h-4 mr-2" />
                Rate Worker
              </button>
            </div>
          )}
        </div>

        {/* Content Tabs */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="border-b border-gray-100">
            <nav className="flex px-4" aria-label="Tabs">
              {[
                { id: 'details', name: 'Details', icon: FileText },
                { id: 'applicants', name: job.type === 'daily' ? `Applicants (${applications.length})` : `Bids (${bids.length})`, icon: Users }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setSelectedTab(tab.id)}
                  className={`flex items-center px-6 py-4 text-sm font-semibold border-b-2 transition-colors ${
                    selectedTab === tab.id
                      ? 'border-orange-500 text-orange-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-200'
                  }`}
                >
                  <tab.icon className="w-4 h-4 mr-2" />
                  {tab.name}
                </button>
              ))}
            </nav>
          </div>

          <div className="p-6 sm:p-8">
            {selectedTab === 'details' ? (
              <div className="space-y-8">
                <div>
                  <h3 className="text-lg font-bold text-gray-900 mb-3">Job Description</h3>
                  <p className="text-gray-600 leading-relaxed text-lg">{job.description}</p>
                </div>

                {job.photos && job.photos.length > 0 && (
                  <div>
                    <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
                      <Camera className="w-5 h-5 mr-2 text-orange-600" />
                      Job Photos
                    </h3>
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                      {job.photos.map((photo, idx) => (
                        <div key={idx} className="aspect-square rounded-xl overflow-hidden border border-gray-100 group cursor-pointer relative shadow-sm">
                          <img 
                            src={photo.startsWith('http') ? photo : `${BACKEND_URL}${photo}`} 
                            alt={`Job work ${idx + 1}`}
                            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="space-y-6">
                {(job.type === 'daily' ? applications : bids).map((item) => (
                  <div key={item.id} className={`p-4 sm:p-6 rounded-2xl border ${item.status === 'accepted' ? 'border-orange-200 bg-orange-50' : 'border-gray-100 hover:border-orange-200 transition-colors'}`}>
                    <div className="flex flex-col sm:flex-row justify-between items-start gap-4">
                      <div className="flex gap-4">
                        <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center">
                          <UserCircle className="w-8 h-8 text-gray-400" />
                        </div>
                        <div>
                          <h4 className="font-bold text-gray-900 mb-1">{item.worker_info?.name || `Worker #${item.worker_id.slice(0, 5)}`}</h4>
                          <div className="flex items-center gap-3">
                            <StarRating 
                              rating={item.worker_info?.rating_avg || 0} 
                              count={item.worker_info?.reviews_count || 0} 
                            />
                            {item.status === 'accepted' && (
                              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-green-100 text-green-800">
                                SELECTED
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="w-full sm:w-auto text-left sm:text-right">
                        {job.type === 'contractual' && (
                          <p className="text-2xl font-bold text-orange-600">₹{item.bid_amount?.toLocaleString()}</p>
                        )}
                        <p className="text-sm text-gray-500">Submitted {new Date(item.created_at).toLocaleDateString()}</p>
                      </div>
                    </div>
                    {item.message && (
                      <p className="mt-4 text-gray-600 bg-white bg-opacity-50 p-4 rounded-xl text-sm italic border border-gray-100 italic">
                        "{item.message}"
                      </p>
                    )}
                    {isCustomer && job.status === 'open' && (
                      <div className="mt-6">
                        <button
                          onClick={() => handleAssignWorker(item.worker_id)}
                          className="w-full sm:w-auto px-6 py-2.5 bg-orange-600 text-white font-bold rounded-xl hover:bg-orange-700 shadow-md hover:shadow-lg transition-all"
                        >
                          {job.type === 'daily' ? 'Hire This Worker' : 'Accept This Bid'}
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
      
      <ReviewModal 
        isOpen={showReviewModal} 
        onClose={() => setShowReviewModal(false)} 
        onSubmit={handleSubmitReview}
        workerName={job.type === 'daily' ? applications.find(a => a.status === 'accepted')?.worker_info?.name : bids.find(b => b.status === 'accepted')?.worker_info?.name}
      />
    </div>
  );
};

// My Jobs Component (Customer View)
const MyJobs = () => {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedStatus, setSelectedStatus] = useState('all');
  const navigate = useNavigate();

  useEffect(() => {
    fetchJobs();
  }, []);

  const fetchJobs = async () => {
    try {
      const response = await axios.get(`${API}/jobs`);
      setJobs(response.data);
    } catch (error) {
      toast.error('Failed to fetch jobs');
    } finally {
      setLoading(false);
    }
  };

  const filteredJobs = jobs.filter(job => {
    if (selectedStatus === 'all') return true;
    return job.status === selectedStatus;
  });

  const getStatusIcon = (status) => {
    switch (status) {
      case 'open': return <Timer className="w-4 h-4" />;
      case 'assigned': return <UserCheck className="w-4 h-4" />;
      case 'completed': return <CheckCircle2 className="w-4 h-4" />;
      case 'cancelled': return <XCircle className="w-4 h-4" />;
      default: return <AlertCircle className="w-4 h-4" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'open': return 'bg-green-100 text-green-800';
      case 'assigned': return 'bg-blue-100 text-blue-800';
      case 'completed': return 'bg-gray-100 text-gray-800';
      case 'cancelled': return 'bg-red-100 text-red-800';
      default: return 'bg-yellow-100 text-yellow-800';
    }
  };

  return (
    <div className="p-6">
      <div className="mb-8">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">My Jobs</h1>
            <p className="text-gray-600">Manage and track all your job postings</p>
          </div>
          <button
            onClick={() => navigate('/post-job')}
            className="flex items-center px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700"
          >
            <Plus className="w-4 h-4 mr-2" />
            Post New Job
          </button>
        </div>

        {/* Status Filter */}
        <div className="flex gap-2 mb-6">
          {[
            { value: 'all', label: 'All Jobs' },
            { value: 'open', label: 'Open' },
            { value: 'assigned', label: 'Assigned' },
            { value: 'completed', label: 'Completed' }
          ].map((filter) => (
            <button
              key={filter.value}
              onClick={() => setSelectedStatus(filter.value)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                selectedStatus === filter.value
                  ? 'bg-orange-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {filter.label}
            </button>
          ))}
        </div>
      </div>

      {/* Jobs List */}
      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-white rounded-lg p-6 animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-1/4 mb-2"></div>
              <div className="h-6 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-4 bg-gray-200 rounded w-full mb-4"></div>
              <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      ) : filteredJobs.length > 0 ? (
        <div className="grid grid-cols-1 gap-6">
          {filteredJobs.map((job) => (
            <div key={job.id} className="bg-white rounded-lg shadow-sm border p-6 hover:shadow-md transition-shadow">
              <div className="flex justify-between items-start mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold text-gray-900">{job.title}</h3>
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                      job.type === 'daily' 
                        ? 'bg-blue-100 text-blue-800' 
                        : 'bg-purple-100 text-purple-800'
                    }`}>
                      {job.type === 'daily' ? (
                        <>
                          <Zap className="w-3 h-3 mr-1" />
                          Daily
                        </>
                      ) : (
                        <>
                          <Target className="w-3 h-3 mr-1" />
                          Contractual
                        </>
                      )}
                    </span>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(job.status)}`}>
                      {getStatusIcon(job.status)}
                      <span className="ml-1 capitalize">{job.status}</span>
                    </span>
                  </div>
                  <p className="text-gray-600 mb-3 line-clamp-2">{job.description}</p>
                  <div className="flex items-center gap-6 text-sm text-gray-500">
                    <div className="flex items-center">
                      <MapPin className="w-4 h-4 mr-1" />
                      {job.location?.address}
                    </div>
                    <div className="flex items-center">
                      <IndianRupee className="w-4 h-4 mr-1" />
                      {job.budget_amount?.toLocaleString()}
                    </div>
                    <div className="flex items-center">
                      <Users className="w-4 h-4 mr-1" />
                      {job.applications_count + job.bids_count} {job.type === 'daily' ? 'applications' : 'bids'}
                    </div>
                    <div className="flex items-center">
                      <Calendar className="w-4 h-4 mr-1" />
                      {new Date(job.created_at).toLocaleDateString()}
                    </div>
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => navigate(`/jobs/${job.id}`)}
                    className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 flex items-center"
                  >
                    <Eye className="w-4 h-4 mr-2" />
                    View Details
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-lg p-12 text-center">
          <Briefcase className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No jobs found</h3>
          <p className="text-gray-500 mb-4">
            {selectedStatus === 'all' 
              ? "You haven't posted any jobs yet." 
              : `No jobs with status: ${selectedStatus}`}
          </p>
          <button
            onClick={() => navigate('/post-job')}
            className="text-orange-600 hover:text-orange-700 font-medium"
          >
            Post your first job
          </button>
        </div>
      )}
    </div>
  );
};

// Job Creation Component (existing code - same as before)
const PostJobForm = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [jobData, setJobData] = useState({
    type: 'daily',
    title: '',
    description: '',
    category: 'skilled',
    location: {
      lat: 28.6139,
      lng: 77.2090,
      address: ''
    },
    preferred_time_window: {
      start: '09:00',
      end: '17:00'
    },
    budget_amount: '',
    is_budget_negotiable: false,
    photos: []
  });
  const [loading, setLoading] = useState(false);
  const [uploadingImage, setUploadingImage] = useState(false);
  const fileInputRef = useRef(null);

  const handleImageUpload = async (e) => {
    const files = Array.from(e.target.files);
    if (files.length === 0) return;

    setUploadingImage(true);
    const newPhotos = [...jobData.photos];

    try {
      for (const file of files) {
        if (file.size > 10 * 1024 * 1024) {
          toast.error(`${file.name} is larger than 10MB`);
          continue;
        }
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await axios.post(`${API}/upload`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        
        newPhotos.push(response.data.url);
      }
      handleInputChange('photos', newPhotos);
      if (newPhotos.length > jobData.photos.length) {
        toast.success('Images uploaded successfully');
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to upload images');
    } finally {
      setUploadingImage(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const removePhoto = (index) => {
    const newPhotos = [...jobData.photos];
    newPhotos.splice(index, 1);
    handleInputChange('photos', newPhotos);
  };

  const categories = [
    { value: 'skilled', label: 'Skilled Work', icon: Wrench, desc: 'Plumbing, electrical, carpentry' },
    { value: 'daily_wage', label: 'Daily Wage', icon: HardHat, desc: 'Construction, cleaning, moving' }
  ];

  const jobTypes = [
    { 
      value: 'daily', 
      label: 'Daily Job', 
      icon: Zap, 
      desc: 'Fixed price work - workers apply',
      features: ['Fixed pricing', 'Quick hiring', 'Same day work']
    },
    { 
      value: 'contractual', 
      label: 'Contractual Job', 
      icon: Target, 
      desc: 'Project-based - workers bid with quotes',
      features: ['Compare multiple bids', 'Negotiate prices', 'Project timeline']
    }
  ];

  const handleInputChange = (field, value) => {
    if (field.includes('.')) {
      const [parent, child] = field.split('.');
      setJobData(prev => ({
        ...prev,
        [parent]: {
          ...prev[parent],
          [child]: value
        }
      }));
    } else {
      setJobData(prev => ({
        ...prev,
        [field]: value
      }));
    }
  };

  const handleSubmit = async () => {
    setLoading(true);
    try {
      // Create job
      const response = await axios.post(`${API}/jobs`, jobData);
      const createdJob = response.data;
      
      // Publish job immediately
      await axios.put(`${API}/jobs/${createdJob.id}/publish`);
      
      toast.success('Job posted successfully!');
      navigate('/my-jobs');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to post job');
    } finally {
      setLoading(false);
    }
  };

  const canProceedToNext = () => {
    switch (step) {
      case 1:
        return jobData.type && jobData.category;
      case 2:
        return jobData.title && jobData.description;
      case 3:
        return jobData.location.address && jobData.budget_amount;
      default:
        return true;
    }
  };

  const renderStep1 = () => (
    <div className="space-y-8">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">What type of job is this?</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {jobTypes.map((type) => (
            <div
              key={type.value}
              onClick={() => handleInputChange('type', type.value)}
              className={`p-6 rounded-xl border-2 cursor-pointer transition-all ${
                jobData.type === type.value
                  ? 'border-orange-500 bg-orange-50'
                  : 'border-gray-200 hover:border-orange-300'
              }`}
            >
              <div className="flex items-center mb-3">
                <type.icon className={`w-8 h-8 mr-3 ${
                  jobData.type === type.value ? 'text-orange-600' : 'text-gray-600'
                }`} />
                <div>
                  <h4 className="font-semibold text-gray-900">{type.label}</h4>
                  <p className="text-sm text-gray-600">{type.desc}</p>
                </div>
              </div>
              <ul className="space-y-1">
                {type.features.map((feature, index) => (
                  <li key={index} className="flex items-center text-sm text-gray-600">
                    <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
                    {feature}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Select job category</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {categories.map((category) => (
            <div
              key={category.value}
              onClick={() => handleInputChange('category', category.value)}
              className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                jobData.category === category.value
                  ? 'border-orange-500 bg-orange-50'
                  : 'border-gray-200 hover:border-orange-300'
              }`}
            >
              <div className="flex items-center">
                <category.icon className={`w-6 h-6 mr-3 ${
                  jobData.category === category.value ? 'text-orange-600' : 'text-gray-600'
                }`} />
                <div>
                  <h4 className="font-medium text-gray-900">{category.label}</h4>
                  <p className="text-sm text-gray-600">{category.desc}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderStep2 = () => (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Job Title *
        </label>
        <input
          type="text"
          value={jobData.title}
          onChange={(e) => handleInputChange('title', e.target.value)}
          placeholder="e.g., Bathroom plumbing repair needed urgently"
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Detailed Description *
        </label>
        <textarea
          value={jobData.description}
          onChange={(e) => handleInputChange('description', e.target.value)}
          rows={4}
          placeholder="Describe the work needed, specific requirements, materials needed, etc."
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Preferred Start Time
          </label>
          <input
            type="time"
            value={jobData.preferred_time_window.start}
            onChange={(e) => handleInputChange('preferred_time_window.start', e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Preferred End Time
          </label>
          <input
            type="time"
            value={jobData.preferred_time_window.end}
            onChange={(e) => handleInputChange('preferred_time_window.end', e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Add Photos (Optional)
        </label>
        <div 
          onClick={() => !uploadingImage && fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${uploadingImage ? 'border-orange-300 bg-orange-50' : 'border-gray-300 hover:border-orange-500'}`}
        >
          {uploadingImage ? (
            <Loader2 className="w-12 h-12 mx-auto mb-4 text-orange-500 animate-spin" />
          ) : (
            <Camera className="w-12 h-12 mx-auto mb-4 text-gray-400" />
          )}
          <p className="text-gray-600 font-medium">{uploadingImage ? 'Uploading Photos...' : 'Click to upload photos of the work area'}</p>
          <p className="text-sm text-gray-500 mt-1">PNG, JPG, WEBP up to 10MB</p>
          <input 
            type="file" 
            multiple 
            accept="image/*" 
            className="hidden" 
            ref={fileInputRef}
            onChange={handleImageUpload}
            disabled={uploadingImage}
          />
        </div>
        {jobData.photos.length > 0 && (
          <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
            {jobData.photos.map((url, idx) => (
              <div key={idx} className="relative group rounded-lg overflow-hidden border border-gray-200">
                <img src={`${BACKEND_URL}${url}`} alt={`Preview ${idx + 1}`} className="w-full h-24 object-cover" />
                <button
                  type="button"
                  onClick={(e) => { e.stopPropagation(); removePhoto(idx); }}
                  className="absolute top-1 right-1 bg-red-500 text-white rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity focus:opacity-100 shadow-sm"
                >
                  <XCircle className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );

  const renderStep3 = () => (
    <div className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Location *
        </label>
        <div className="relative">
          <MapPin className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
          <input
            type="text"
            value={jobData.location.address}
            onChange={(e) => handleInputChange('location.address', e.target.value)}
            placeholder="Enter your location address"
            className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
          />
        </div>
        <p className="text-sm text-gray-500 mt-1">
          📍 Google Maps integration will be added for precise location selection
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Budget Amount *
        </label>
        <div className="relative">
          <IndianRupee className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
          <input
            type="number"
            value={jobData.budget_amount}
            onChange={(e) => handleInputChange('budget_amount', parseFloat(e.target.value) || '')}
            placeholder={jobData.type === 'daily' ? 'Fixed amount' : 'Expected budget range'}
            className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
          />
        </div>
        {jobData.type === 'daily' ? (
          <p className="text-sm text-gray-600 mt-1">
            💰 This will be the fixed amount workers see for this daily job
          </p>
        ) : (
          <div className="mt-3">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={jobData.is_budget_negotiable}
                onChange={(e) => handleInputChange('is_budget_negotiable', e.target.checked)}
                className="mr-2"
              />
              <span className="text-sm text-gray-700">Budget is negotiable</span>
            </label>
            <p className="text-sm text-gray-600 mt-1">
              💡 Workers can bid above or below this amount for contractual jobs
            </p>
          </div>
        )}
      </div>

      <div className="bg-orange-50 rounded-lg p-4">
        <h4 className="font-medium text-orange-800 mb-2">Job Summary</h4>
        <div className="space-y-2 text-sm text-orange-700">
          <p><strong>Type:</strong> {jobTypes.find(t => t.value === jobData.type)?.label}</p>
          <p><strong>Category:</strong> {categories.find(c => c.value === jobData.category)?.label}</p>
          <p><strong>Title:</strong> {jobData.title}</p>
          <p><strong>Budget:</strong> ₹{jobData.budget_amount}</p>
          <p><strong>Location:</strong> {jobData.location.address}</p>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <button 
              onClick={() => navigate('/dashboard')}
              className="flex items-center text-gray-600 hover:text-gray-900"
            >
              <ArrowLeft className="w-5 h-5 mr-2" />
              Back to Dashboard
            </button>
            <span className="text-sm text-gray-500">Step {step} of 3</span>
          </div>
          
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Post a New Job</h1>
          <p className="text-gray-600">Find the right worker for your needs</p>

          {/* Progress bar */}
          <div className="flex mt-6">
            {[1, 2, 3].map((s) => (
              <div key={s} className="flex-1">
                <div className={`h-2 rounded-full ${
                  s <= step ? 'bg-orange-500' : 'bg-gray-200'
                } ${s < 3 ? 'mr-2' : ''}`} />
              </div>
            ))}
          </div>
        </div>

        {/* Form Content */}
        <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
          {step === 1 && renderStep1()}
          {step === 2 && renderStep2()}
          {step === 3 && renderStep3()}
        </div>

        {/* Navigation */}
        <div className="flex justify-between">
          <button
            onClick={() => setStep(step - 1)}
            disabled={step === 1}
            className={`px-6 py-3 rounded-lg font-medium ${
              step === 1
                ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Previous
          </button>
          
          {step < 3 ? (
            <button
              onClick={() => setStep(step + 1)}
              disabled={!canProceedToNext()}
              className={`px-6 py-3 rounded-lg font-medium ${
                canProceedToNext()
                  ? 'bg-orange-600 text-white hover:bg-orange-700'
                  : 'bg-gray-200 text-gray-400 cursor-not-allowed'
              }`}
            >
              Next Step
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={loading || !canProceedToNext()}
              className="px-8 py-3 bg-orange-600 text-white rounded-lg font-medium hover:bg-orange-700 disabled:opacity-50"
            >
              {loading ? 'Posting Job...' : 'Post Job'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

// Find Jobs Component (Worker View) - Enhanced with bidding
const FindJobs = () => {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [biddingJob, setBiddingJob] = useState(null);
  const [filters, setFilters] = useState({
    type: '',
    category: '',
    search: '',
    sortBy: 'recent'
  });

  useEffect(() => {
    fetchJobs();
  }, [filters]);

  const fetchJobs = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filters.type) params.append('type', filters.type);
      if (filters.category) params.append('category', filters.category);
      params.append('status', 'open');

      const response = await axios.get(`${API}/jobs?${params.toString()}`);
      let jobsData = response.data;

      // Apply search filter
      if (filters.search) {
        const searchTerm = filters.search.toLowerCase();
        jobsData = jobsData.filter(job => 
          job.title.toLowerCase().includes(searchTerm) ||
          job.description.toLowerCase().includes(searchTerm)
        );
      }

      // Apply sorting
      if (filters.sortBy === 'budget_high') {
        jobsData.sort((a, b) => b.budget_amount - a.budget_amount);
      } else if (filters.sortBy === 'budget_low') {
        jobsData.sort((a, b) => a.budget_amount - b.budget_amount);
      } else {
        jobsData.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
      }

      setJobs(jobsData);
    } catch (error) {
      toast.error('Failed to fetch jobs');
    } finally {
      setLoading(false);
    }
  };

  const handleApply = async (jobId, jobType) => {
    try {
      if (jobType === 'daily') {
        // Apply to daily job
        await axios.post(`${API}/jobs/${jobId}/apply`, {
          message: "I am interested in this job and available to start immediately."
        });
        toast.success('Application submitted successfully!');
      } else {
        // Open bidding modal for contractual jobs
        const job = jobs.find(j => j.id === jobId);
        setBiddingJob(job);
        return;
      }
      fetchJobs(); // Refresh to update application counts
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to apply');
    }
  };

  const JobCard = ({ job }) => (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
              job.type === 'daily' 
                ? 'bg-blue-100 text-blue-800' 
                : 'bg-purple-100 text-purple-800'
            }`}>
              {job.type === 'daily' ? (
                <>
                  <Zap className="w-3 h-3 mr-1" />
                  Daily Job
                </>
              ) : (
                <>
                  <Target className="w-3 h-3 mr-1" />
                  Contractual
                </>
              )}
            </span>
            <span className="text-xs text-gray-500 capitalize">{job.category}</span>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">{job.title}</h3>
          <p className="text-gray-600 text-sm line-clamp-2 mb-3">{job.description}</p>
        </div>
        {job.photos && job.photos.length > 0 && (
          <div className="ml-4 flex-shrink-0 w-24 h-24 rounded-lg overflow-hidden border border-gray-100">
            <img 
              src={job.photos[0].startsWith('http') ? job.photos[0] : `${BACKEND_URL}${job.photos[0]}`} 
              alt="Job preview" 
              className="w-full h-full object-cover"
              onError={(e) => {
                e.target.style.display = 'none';
              }}
            />
          </div>
        )}
        <div className="text-right ml-4">
          <div className="text-xl font-bold text-orange-600">₹{job.budget_amount.toLocaleString()}</div>
          {job.is_budget_negotiable && (
            <span className="text-xs text-green-600">Negotiable</span>
          )}
        </div>
      </div>

      <div className="flex items-center text-sm text-gray-500 mb-4">
        <MapPin className="w-4 h-4 mr-1" />
        <span className="mr-4">{job.location?.address || 'Location not specified'}</span>
        <Clock className="w-4 h-4 mr-1" />
        <span>{job.preferred_time_window?.start} - {job.preferred_time_window?.end}</span>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4 text-sm text-gray-500">
          <span>{job.applications_count + job.bids_count} {job.type === 'daily' ? 'applications' : 'bids'}</span>
          <span>Posted {new Date(job.created_at).toLocaleDateString()}</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => navigate(`/jobs/${job.id}`)}
            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors flex items-center"
          >
            <Eye className="w-4 h-4 mr-2" />
            Details
          </button>
          <button
            onClick={() => handleApply(job.id, job.type)}
            className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors flex items-center"
          >
            {job.type === 'daily' ? (
              <>
                <Send className="w-4 h-4 mr-2" />
                Apply Now
              </>
            ) : (
              <>
                <DollarSign className="w-4 h-4 mr-2" />
                Place Bid
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Find Jobs</h1>
        <p className="text-gray-600">Discover work opportunities in your area</p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Search</label>
            <input
              type="text"
              value={filters.search}
              onChange={(e) => setFilters({...filters, search: e.target.value})}
              placeholder="Search jobs..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-orange-500 focus:border-orange-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Job Type</label>
            <select
              value={filters.type}
              onChange={(e) => setFilters({...filters, type: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-orange-500 focus:border-orange-500"
            >
              <option value="">All Types</option>
              <option value="daily">Daily Jobs</option>
              <option value="contractual">Contractual</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Category</label>
            <select
              value={filters.category}
              onChange={(e) => setFilters({...filters, category: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-orange-500 focus:border-orange-500"
            >
              <option value="">All Categories</option>
              <option value="skilled">Skilled Work</option>
              <option value="daily_wage">Daily Wage</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Sort By</label>
            <select
              value={filters.sortBy}
              onChange={(e) => setFilters({...filters, sortBy: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-orange-500 focus:border-orange-500"
            >
              <option value="recent">Most Recent</option>
              <option value="budget_high">Highest Budget</option>
              <option value="budget_low">Lowest Budget</option>
            </select>
          </div>
        </div>
      </div>

      {/* Jobs List */}
      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-white rounded-lg p-6 animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-1/4 mb-2"></div>
              <div className="h-6 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-4 bg-gray-200 rounded w-full mb-4"></div>
              <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      ) : jobs.length > 0 ? (
        <div className="space-y-4">
          {jobs.map((job) => (
            <JobCard key={job.id} job={job} />
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-lg p-12 text-center">
          <Briefcase className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No jobs found</h3>
          <p className="text-gray-500 mb-4">Try adjusting your filters to see more jobs.</p>
          <button
            onClick={() => setFilters({ type: '', category: '', search: '', sortBy: 'recent' })}
            className="text-orange-600 hover:text-orange-700 font-medium"
          >
            Clear all filters
          </button>
        </div>
      )}

      {/* Bidding Modal */}
      <BiddingModal
        job={biddingJob}
        isOpen={!!biddingJob}
        onClose={() => setBiddingJob(null)}
        onSuccess={fetchJobs}
      />
    </div>
  );
};

// Auth Pages (existing code - same as before)
const AuthPage = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    name: '',
    phone: '',
    email: '',
    password: '',
    role: 'customer'
  });
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const endpoint = isLogin ? '/auth/login' : '/auth/register';
      const data = isLogin 
        ? { phone: formData.phone, password: formData.password }
        : formData;

      const response = await axios.post(`${API}${endpoint}`, data);
      login(response.data);
      toast.success(isLogin ? 'Logged in successfully!' : 'Account created successfully!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-amber-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-orange-600 mb-2">Sanyuth</h1>
          <p className="text-gray-600">AI Powered - Blue Collar Marketplace</p>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-8">
          <div className="flex mb-6 bg-gray-100 rounded-lg p-1">
            <button
              className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                isLogin ? 'bg-white shadow-sm text-gray-900' : 'text-gray-500'
              }`}
              onClick={() => setIsLogin(true)}
            >
              Login
            </button>
            <button
              className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                !isLogin ? 'bg-white shadow-sm text-gray-900' : 'text-gray-500'
              }`}
              onClick={() => setIsLogin(false)}
            >
              Sign Up
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                  <input
                    type="text"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
                  <select
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                    value={formData.role}
                    onChange={(e) => setFormData({...formData, role: e.target.value})}
                  >
                    <option value="customer">Customer</option>
                    <option value="worker">Worker</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email (Optional)</label>
                  <input
                    type="email"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                    value={formData.email}
                    onChange={(e) => setFormData({...formData, email: e.target.value})}
                  />
                </div>
              </>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Phone Number</label>
              <input
                type="tel"
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                value={formData.phone}
                onChange={(e) => setFormData({...formData, phone: e.target.value})}
                placeholder="Enter your phone number"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
              <input
                type="password"
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-orange-600 text-white py-2 px-4 rounded-md hover:bg-orange-700 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-2 disabled:opacity-50 transition-colors"
            >
              {loading ? 'Processing...' : (isLogin ? 'Login' : 'Create Account')}
            </button>
          </form>

          {isLogin && (
            <div className="mt-6 text-center">
              <p className="text-sm text-gray-600">
                Demo Accounts:
              </p>
              <div className="mt-2 text-xs text-gray-500 space-y-1">
                <div>Customer: 9876543210 / password123</div>
                <div>Worker: 9876543211 / password123</div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Dashboard Components (existing code - same as before)
const CustomerDashboard = () => {
  const [jobs, setJobs] = useState([]);
  const [stats, setStats] = useState({
    totalJobs: 0,
    activeJobs: 0,
    completedJobs: 0,
    totalApplications: 0
  });
  const navigate = useNavigate();

  useEffect(() => {
    fetchJobs();
  }, []);

  const fetchJobs = async () => {
    try {
      const response = await axios.get(`${API}/jobs`);
      setJobs(response.data);
      
      // Calculate stats
      const total = response.data.length;
      const active = response.data.filter(job => ['open', 'assigned', 'in_progress'].includes(job.status)).length;
      const completed = response.data.filter(job => job.status === 'completed').length;
      const totalApps = response.data.reduce((sum, job) => sum + job.applications_count + job.bids_count, 0);
      
      setStats({
        totalJobs: total,
        activeJobs: active,
        completedJobs: completed,
        totalApplications: totalApps
      });
    } catch (error) {
      toast.error('Failed to fetch jobs');
    }
  };

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Customer Dashboard</h1>
        <p className="text-gray-600">Manage your job postings and track applications</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-sm p-6 border border-orange-100">
          <div className="flex items-center">
            <div className="p-2 bg-orange-100 rounded-lg">
              <Briefcase className="w-6 h-6 text-orange-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Jobs</p>
              <p className="text-2xl font-bold text-gray-900">{stats.totalJobs}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6 border border-orange-100">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Clock className="w-6 h-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Active Jobs</p>
              <p className="text-2xl font-bold text-gray-900">{stats.activeJobs}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6 border border-orange-100">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg">
              <CheckCircle className="w-6 h-6 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Completed</p>
              <p className="text-2xl font-bold text-gray-900">{stats.completedJobs}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6 border border-orange-100">
          <div className="flex items-center">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Users className="w-6 h-6 text-purple-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Applications</p>
              <p className="text-2xl font-bold text-gray-900">{stats.totalApplications}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow-sm p-6 mb-8 border border-orange-100">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="flex flex-wrap gap-4">
          <button 
            onClick={() => navigate('/post-job')}
            className="flex items-center px-4 py-2 bg-orange-600 text-white rounded-md hover:bg-orange-700 transition-colors"
          >
            <Plus className="w-4 h-4 mr-2" />
            Post New Job
          </button>
          <button 
            onClick={() => navigate('/my-jobs')}
            className="flex items-center px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors"
          >
            <Briefcase className="w-4 h-4 mr-2" />
            Manage Jobs
          </button>
          <button 
            onClick={() => navigate('/messages')}
            className="flex items-center px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors"
          >
            <MessageCircle className="w-4 h-4 mr-2" />
            View Messages
          </button>
        </div>
      </div>

      {/* Recent Jobs */}
      <div className="bg-white rounded-lg shadow-sm border border-orange-100">
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
          <h2 className="text-lg font-semibold text-gray-900">Recent Jobs</h2>
          <button
            onClick={() => navigate('/my-jobs')}
            className="text-orange-600 hover:text-orange-700 text-sm font-medium"
          >
            View All
          </button>
        </div>
        <div className="divide-y divide-gray-200">
          {jobs.slice(0, 5).map((job) => (
            <div 
              key={job.id} 
              className="px-6 py-4 hover:bg-gray-50 cursor-pointer"
              onClick={() => navigate(`/jobs/${job.id}`)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center flex-1">
                  {job.photos && job.photos.length > 0 && (
                    <div className="w-12 h-12 rounded-md overflow-hidden bg-gray-100 mr-4 flex-shrink-0">
                      <img 
                        src={job.photos[0].startsWith('http') ? job.photos[0] : `${BACKEND_URL}${job.photos[0]}`} 
                        alt="Job" 
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          e.target.parentNode.style.display = 'none';
                        }}
                      />
                    </div>
                  )}
                  <div className="flex-1">
                    <h3 className="text-sm font-medium text-gray-900">{job.title}</h3>
                  <div className="flex items-center mt-1 space-x-4">
                    <div className="flex items-center text-sm text-gray-500">
                      <MapPin className="w-4 h-4 mr-1" />
                      {job.location?.address}
                    </div>
                    <div className="flex items-center text-sm text-gray-500">
                      <IndianRupee className="w-4 h-4 mr-1" />
                      {job.budget_amount}
                    </div>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      job.status === 'open' ? 'bg-green-100 text-green-800' :
                      job.status === 'assigned' ? 'bg-blue-100 text-blue-800' :
                      job.status === 'completed' ? 'bg-gray-100 text-gray-800' :
                      'bg-yellow-100 text-yellow-800'
                    }`}>
                      {job.status}
                    </span>
                  </div>
                </div>
              </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-gray-900">
                    {job.applications_count + job.bids_count} {job.type === 'daily' ? 'Applications' : 'Bids'}
                  </p>
                  <p className="text-xs text-gray-500 capitalize">{job.type} Job</p>
                </div>
              </div>
            </div>
          ))}
        </div>
        {jobs.length === 0 && (
          <div className="px-6 py-8 text-center">
            <Briefcase className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">No jobs posted yet</p>
            <button 
              onClick={() => navigate('/post-job')}
              className="mt-4 text-orange-600 hover:text-orange-700 font-medium"
            >
              Post your first job
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

const WorkerDashboard = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState({
    stats: {
      availableJobs: 0,
      appliedJobs: 0,
      activeJobs: 0,
      profileCompletion: 85,
    },
    recentApplications: []
  });

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/worker/dashboard-data`);
      setData(response.data);
    } catch (error) {
      console.error('Failed to fetch worker dashboard data:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };
  
  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[1, 2, 3].map(i => <div key={i} className="h-48 bg-gray-100 rounded-lg shadow-sm border"></div>)}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Worker Dashboard</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Available Jobs</h2>
            <Search className="w-5 h-5 text-orange-400" />
          </div>
          <p className="text-3xl font-bold text-orange-600">{data.stats.availableJobs}</p>
          <p className="text-gray-600 text-sm mb-4">In your area</p>
          <button 
            onClick={() => navigate('/find-jobs')}
            className="w-full bg-orange-600 text-white py-2 px-4 rounded-md hover:bg-orange-700 transition-colors"
          >
            Browse Jobs
          </button>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Applied Jobs</h2>
            <Calendar className="w-5 h-5 text-blue-400" />
          </div>
          <p className="text-3xl font-bold text-blue-600">{data.stats.appliedJobs}</p>
          <p className="text-gray-600 text-sm mb-4">Total applications & bids</p>
          <button 
            onClick={() => document.getElementById('recent-apps')?.scrollIntoView({ behavior: 'smooth' })}
            className="w-full border border-gray-300 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-50 transition-colors"
          >
            View Applications
          </button>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow-sm border">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Reputation</h2>
            <Star className="w-5 h-5 text-yellow-500" />
          </div>
          <div className="flex items-end gap-2 mb-1">
            <p className="text-3xl font-bold text-gray-900">{data.stats.ratingAvg?.toFixed(1) || '0.0'}</p>
            <div className="mb-1.5">
              <StarRating rating={data.stats.ratingAvg || 0} />
            </div>
          </div>
          <p className="text-gray-600 text-sm mb-4">From {data.stats.reviewsCount || 0} reviews</p>
          <div className="w-full bg-gray-100 h-2 rounded-full overflow-hidden">
            <div 
              className="bg-yellow-400 h-full transition-all duration-500" 
              style={{ width: `${(data.stats.ratingAvg || 0) * 20}%` }}
            ></div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Recent Applications Section */}
        <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50">
            <h2 className="text-lg font-bold text-gray-900">Recent Applications</h2>
            <button 
              onClick={() => navigate('/my-jobs')}
              className="text-sm text-orange-600 font-semibold hover:text-orange-700"
            >
              View All
            </button>
          </div>
          <div className="divide-y divide-gray-100">
            {data.recentApplications && data.recentApplications.map((app) => (
              <div 
                key={app.id} 
                className="p-4 hover:bg-gray-50 transition-colors cursor-pointer group"
                onClick={() => navigate(`/jobs/${app.id}`)}
              >
                <div className="flex justify-between items-center">
                  <div>
                    <h3 className="font-bold text-gray-900 group-hover:text-orange-600 transition-colors">{app.title}</h3>
                    <div className="flex items-center gap-3 mt-1">
                      <span className="text-sm text-gray-500">₹{app.budget_amount?.toLocaleString()}</span>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${
                        app.application_status === 'accepted' ? 'bg-green-100 text-green-700' :
                        app.application_status === 'rejected' ? 'bg-red-100 text-red-700' :
                        'bg-blue-100 text-blue-700'
                      }`}>
                        {app.application_status}
                      </span>
                    </div>
                  </div>
                  <ChevronRight className="w-5 h-5 text-gray-300 group-hover:text-orange-400 group-hover:translate-x-1 transition-all" />
                </div>
              </div>
            ))}
            {(!data.recentApplications || data.recentApplications.length === 0) && (
              <div className="p-8 text-center text-gray-500 italic">
                You haven't applied to any jobs yet.
              </div>
            )}
          </div>
        </div>

        {/* Recent Reviews Section */}
        <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50">
            <h2 className="text-lg font-bold text-gray-900">Latest Feedback</h2>
            <div className="flex items-center text-yellow-700 bg-yellow-50 px-2 py-1 rounded text-xs font-bold ring-1 ring-yellow-200">
              <Star className="w-3 h-3 mr-1 fill-current" />
              {data.stats.ratingAvg?.toFixed(1) || '0.0'}
            </div>
          </div>
          <div className="divide-y divide-gray-100">
            {data.recentReviews && data.recentReviews.length > 0 ? (
              data.recentReviews.map((review, idx) => (
                <div key={idx} className="p-4 space-y-2">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="text-sm font-bold text-gray-900">{review.reviewer_name}</p>
                      <StarRating rating={review.stars} />
                    </div>
                    <span className="text-[10px] text-gray-400 font-medium">
                      {new Date(review.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  {review.comment && (
                    <p className="text-gray-600 text-sm italic leading-relaxed bg-gray-50 p-3 rounded-lg border-l-4 border-yellow-400">
                      "{review.comment}"
                    </p>
                  )}
                </div>
              ))
            ) : (
              <div className="p-12 text-center">
                <div className="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4 border border-dashed border-gray-300">
                  <Star className="w-8 h-8 text-gray-300" />
                </div>
                <p className="text-gray-500 text-sm italic">No reviews yet. Complete jobs to build your reputation!</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// Main App Layout
const AppLayout = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeRoute, setActiveRoute] = useState('dashboard');

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar 
        isOpen={sidebarOpen} 
        onClose={() => setSidebarOpen(false)} 
        activeRoute={activeRoute}
        setActiveRoute={setActiveRoute}
      />
      
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header onMenuClick={() => setSidebarOpen(true)} />
        
        <main className="flex-1 overflow-x-hidden overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  );
};

// Protected Route Component
const ProtectedRoute = ({ children, requiredRole }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-600"></div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/auth" replace />;
  }

  if (requiredRole && user.role !== requiredRole) {
    return <Navigate to="/dashboard" replace />;
  }

  return <AppLayout>{children}</AppLayout>;
};

// Main App Component
function App() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gradient-to-br from-orange-50 to-amber-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-600 mx-auto mb-4"></div>
          <h2 className="text-xl font-semibold text-orange-600">Sanyuth</h2>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          {/* Regular User Authentication */}
          <Route 
            path="/auth" 
            element={user ? <Navigate to="/dashboard" replace /> : <AuthPage />} 
          />

          {/* Admin Login - Separate URL */}
          <Route 
            path="/admin-login" 
            element={user?.role === 'admin' ? <Navigate to="/admin/dashboard" replace /> : <AdminLogin />} 
          />
          
          {/* User Dashboards */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                {user?.role === 'customer' && <CustomerDashboard />}
                {user?.role === 'worker' && <WorkerDashboard />}
                {user?.role === 'admin' && <Navigate to="/admin/dashboard" replace />}
              </ProtectedRoute>
            }
          />

          {/* Customer Routes */}
          <Route
            path="/post-job"
            element={
              <ProtectedRoute requiredRole="customer">
                <PostJobForm />
              </ProtectedRoute>
            }
          />

          <Route
            path="/my-jobs"
            element={
              <ProtectedRoute requiredRole="customer">
                <MyJobs />
              </ProtectedRoute>
            }
          />

          <Route
            path="/jobs/:jobId"
            element={
              <ProtectedRoute>
                <JobDetails />
              </ProtectedRoute>
            }
          />

          {/* Worker Routes */}
          <Route
            path="/find-jobs"
            element={
              <ProtectedRoute requiredRole="worker">
                <FindJobs />
              </ProtectedRoute>
            }
          />

          <Route
            path="/profile"
            element={
              <ProtectedRoute requiredRole="worker">
                <WorkerProfile />
              </ProtectedRoute>
            }
          />

          {/* Admin Routes - Separate Portal */}
          <Route
            path="/admin/dashboard"
            element={
              <ProtectedRoute requiredRole="admin">
                <AdminDashboardComponent />
              </ProtectedRoute>
            }
          />

          <Route
            path="/admin/users"
            element={
              <ProtectedRoute requiredRole="admin">
                <AdminUserManagementComponent />
              </ProtectedRoute>
            }
          />

          <Route
            path="/admin/disputes"
            element={
              <ProtectedRoute requiredRole="admin">
                <AdminDisputeManagementComponent />
              </ProtectedRoute>
            }
          />

          <Route
            path="/admin/analytics"
            element={
              <ProtectedRoute requiredRole="admin">
                <AdminAnalyticsComponent />
              </ProtectedRoute>
            }
          />

          {/* Messaging Routes */}
          <Route
            path="/messages"
            element={
              <ProtectedRoute>
                <MessagingHub user={user} />
              </ProtectedRoute>
            }
          />

          {/* Default Routes */}
          <Route
            path="/"
            element={
              user ? (
                user.role === 'admin' ? <Navigate to="/admin/dashboard" replace /> : <Navigate to="/dashboard" replace />
              ) : <Navigate to="/auth" replace />
            }
          />

          {/* Admin Access */}
          <Route
            path="/admin"
            element={<Navigate to="/admin-login" replace />}
          />
          
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
      
      <Toaster 
        position="top-right"
        toastOptions={{
          duration: 3000,
          style: {
            background: '#fff',
            color: '#374151',
            border: '1px solid #d1d5db'
          }
        }}
      />
    </div>
  );
}

// Wrap App with AuthProvider
export default function AppWithAuth() {
  return (
    <AuthProvider>
      <App />
    </AuthProvider>
  );
}
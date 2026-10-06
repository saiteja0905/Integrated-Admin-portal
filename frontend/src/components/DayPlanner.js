import React, { useState, useEffect } from 'react';
import { 
  Calendar, 
  Clock, 
  MapPin, 
  Navigation, 
  IndianRupee, 
  Briefcase, 
  Zap, 
  Sparkles, 
  ChevronRight,
  CheckCircle2
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';
import { API, getErrorMessage } from '../lib/api';

export const DayPlanner = () => {
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [biddingJobId, setBiddingJobId] = useState(null);

  useEffect(() => {
    fetchDayPlan();
  }, []);

  const fetchDayPlan = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const res = await axios.get(`${API}/planner/day-plan`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPlan(res.data);
    } catch (err) {
      console.error(err);
      toast.error(getErrorMessage(err, 'Failed to load Day Planner schedule'));
    } finally {
      setLoading(false);
    }
  };

  const handleQuickBid = async (suggestion) => {
    try {
      setBiddingJobId(suggestion.job_id);
      const token = localStorage.getItem('token');
      await axios.post(
        `${API}/planner/quick-bid`,
        {
          job_id: suggestion.job_id,
          bid_amount: suggestion.estimated_earnings,
          visiting_charge: 0,
          message: '1-Tap Day Planner Bid for nearby schedule slot'
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('⚡ 1-Tap Bid placed on suggested job!');
      fetchDayPlan();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to place quick bid'));
    } finally {
      setBiddingJobId(null);
    }
  };

  if (loading) {
    return (
      <div className="p-6 max-w-4xl mx-auto space-y-4 animate-pulse">
        <div className="h-8 bg-gray-200 rounded w-1/3"></div>
        <div className="h-32 bg-gray-100 rounded-xl"></div>
        <div className="h-32 bg-gray-100 rounded-xl"></div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-wrap justify-between items-center gap-4 bg-gradient-to-r from-gray-900 to-gray-800 p-6 rounded-2xl text-white shadow-xl">
        <div>
          <div className="flex items-center space-x-2">
            <Calendar className="w-5 h-5 text-orange-400" />
            <span className="text-sm text-gray-300 font-semibold">{plan?.date || 'Today\'s Schedule'}</span>
          </div>
          <h1 className="text-2xl font-bold mt-1">Worker Day Planner</h1>
          <p className="text-xs text-gray-400 mt-1">Optimized job chain & travel route for maximum daily earnings</p>
        </div>

        <div className="flex items-center space-x-6 text-right">
          <div>
            <span className="text-xs text-gray-400 block font-medium">Daily Earnings Target</span>
            <span className="text-2xl font-bold text-emerald-400 flex items-center justify-end">
              <IndianRupee className="w-5 h-5 mr-0.5" />
              {plan?.total_estimated_earnings?.toLocaleString() || 0}
            </span>
          </div>
          <div>
            <span className="text-xs text-gray-400 block font-medium">Scheduled Jobs</span>
            <span className="text-2xl font-bold text-orange-400">{plan?.total_jobs_count || 0}</span>
          </div>
        </div>
      </div>

      {/* Timeline Section */}
      <div className="space-y-6">
        <h2 className="text-lg font-bold text-gray-900 flex items-center">
          <Clock className="w-5 h-5 mr-2 text-orange-600" />
          Today's Interactive Timeline
        </h2>

        {(!plan?.timeline || plan.timeline.length === 0) ? (
          <div className="p-8 text-center bg-gray-50 border border-dashed border-gray-300 rounded-2xl">
            <Briefcase className="w-10 h-10 text-gray-400 mx-auto mb-2" />
            <p className="text-sm font-semibold text-gray-600">No scheduled jobs for today yet.</p>
            <p className="text-xs text-gray-400 mt-1">Check the suggested nearby jobs below to start chaining your day!</p>
          </div>
        ) : (
          <div className="relative border-l-2 border-orange-200 ml-4 space-y-6 pl-6">
            {plan.timeline.map((item, idx) => (
              <div key={idx} className="relative group">
                {/* Timeline Dot */}
                <div className={`absolute -left-[31px] top-4 w-4 h-4 rounded-full border-2 border-white shadow-sm ${
                  item.type === 'job' ? 'bg-orange-600' : 'bg-blue-500'
                }`}></div>

                {item.type === 'job' ? (
                  <div className="bg-white p-5 rounded-2xl border border-gray-200 shadow-sm hover:shadow-md transition">
                    <div className="flex flex-wrap justify-between items-start gap-2 mb-2">
                      <div>
                        <span className="text-xs font-bold text-orange-600 uppercase tracking-wider">{item.start_time} - {item.end_time}</span>
                        <h3 className="text-lg font-bold text-gray-900">{item.title}</h3>
                      </div>
                      <span className="text-lg font-extrabold text-emerald-600 flex items-center">
                        <IndianRupee className="w-4 h-4" />
                        {item.estimated_earnings}
                      </span>
                    </div>

                    <div className="flex items-center text-xs text-gray-500 space-x-4 mt-3">
                      <span className="flex items-center"><MapPin className="w-3.5 h-3.5 mr-1 text-gray-400" />{item.location}</span>
                      <span className="flex items-center"><Clock className="w-3.5 h-3.5 mr-1 text-gray-400" />{item.estimated_duration_minutes} mins duration</span>
                    </div>
                  </div>
                ) : (
                  <div className="bg-blue-50/70 p-3 rounded-xl border border-blue-100 flex items-center justify-between text-xs text-blue-900">
                    <div className="flex items-center space-x-2">
                      <Navigation className="w-4 h-4 text-blue-600" />
                      <span className="font-semibold">{item.title}</span>
                    </div>
                    <div className="flex items-center space-x-3 text-blue-700">
                      <span>📏 {item.distance_km} km</span>
                      <span>⏱️ ~{item.travel_time_minutes} mins travel</span>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Suggested Jobs Chaining Section */}
      {plan?.suggested_jobs?.length > 0 && (
        <div className="bg-gradient-to-br from-orange-50 via-amber-50 to-white p-6 rounded-2xl border border-orange-200 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-orange-700 flex items-center">
                <Sparkles className="w-4 h-4 mr-1 text-orange-500" /> Smart Job Chaining
              </span>
              <h3 className="text-xl font-bold text-gray-900">Suggested Nearby Jobs For Free Slots</h3>
            </div>
            <span className="text-xs bg-orange-100 text-orange-800 font-bold px-3 py-1 rounded-full">
              {plan.suggested_jobs.length} Matches Nearby
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            {plan.suggested_jobs.map((sugg) => (
              <div key={sugg.job_id} className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm hover:border-orange-300 transition space-y-3">
                <div className="flex justify-between items-start">
                  <div>
                    <span className="text-xs font-semibold px-2 py-0.5 bg-gray-100 text-gray-700 rounded">{sugg.category}</span>
                    <h4 className="text-base font-bold text-gray-900 mt-1">{sugg.title}</h4>
                  </div>
                  <span className="text-base font-bold text-emerald-600">₹{sugg.estimated_earnings}</span>
                </div>

                <div className="space-y-1 text-xs text-gray-600">
                  <div className="flex items-center"><MapPin className="w-3.5 h-3.5 mr-1 text-orange-500" />{sugg.location} ({sugg.distance_km} km away)</div>
                  <div className="flex items-center"><Clock className="w-3.5 h-3.5 mr-1 text-gray-400" />Fits open window ~{sugg.start_time}</div>
                </div>

                <button
                  onClick={() => handleQuickBid(sugg)}
                  disabled={biddingJobId === sugg.job_id}
                  className="w-full py-2.5 bg-orange-600 hover:bg-orange-700 text-white rounded-lg text-xs font-bold transition flex items-center justify-center shadow-sm"
                >
                  <Zap className="w-3.5 h-3.5 mr-1.5 fill-current" />
                  {biddingJobId === sugg.job_id ? 'Placing Bid...' : '1-Tap Quick Bid'}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

import React, { useState, useEffect } from 'react';
import { ShieldCheck, Sparkles, Award, CheckCircle2 } from 'lucide-react';
import axios from 'axios';
import { API } from '../lib/api';

export const FairStartBadge = ({ isNewWorker = true, completedJobs = 0 }) => {
  if (!isNewWorker && completedJobs >= 5) {
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800">
        <Award className="w-3.5 h-3.5 mr-1 text-blue-600" />
        Experienced Worker ({completedJobs}+ jobs)
      </span>
    );
  }

  return (
    <div className="flex flex-wrap items-center gap-1.5">
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-100 text-amber-900 border border-amber-300">
        <Sparkles className="w-3.5 h-3.5 mr-1 text-amber-600 fill-current" />
        New on Sanyuth
      </span>

      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800">
        <ShieldCheck className="w-3.5 h-3.5 mr-1 text-emerald-600" />
        ID Verified
      </span>

      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-purple-100 text-purple-800">
        🏷️ Intro Price
      </span>
    </div>
  );
};

export const FairStartWorkerProgress = () => {
  const [eligibility, setEligibility] = useState(null);

  useEffect(() => {
    fetchEligibility();
  }, []);

  const fetchEligibility = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await axios.get(`${API}/fair-start/eligibility`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setEligibility(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  if (!eligibility) return null;

  const completed = eligibility.completed_jobs || 0;
  const percent = Math.min(100, (completed / 5) * 100);

  return (
    <div className="bg-gradient-to-r from-amber-50 to-orange-50 p-4 rounded-xl border border-amber-200 shadow-sm space-y-2">
      <div className="flex justify-between items-center">
        <div className="flex items-center space-x-2">
          <Sparkles className="w-4 h-4 text-amber-600 fill-current" />
          <span className="text-sm font-bold text-gray-900">Fair Start Program</span>
        </div>
        <span className="text-xs font-extrabold text-amber-800 px-2 py-0.5 bg-amber-200 rounded-full">
          {completed} / 5 Introductory Jobs Completed
        </span>
      </div>

      <div className="w-full bg-gray-200 h-2.5 rounded-full overflow-hidden">
        <div 
          className="bg-amber-500 h-full rounded-full transition-all duration-500" 
          style={{ width: `${percent}%` }}
        ></div>
      </div>

      <p className="text-xs text-gray-600">
        {eligibility.is_eligible 
          ? `You are in your Fair Start period! One bid position is reserved for you on matching jobs.` 
          : `Congratulations! You have completed 5 successful jobs and unlocked standard marketplace bidding.`}
      </p>
    </div>
  );
};

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { MessageCircle, Briefcase } from 'lucide-react';
import { ChatSystem } from './ChatSystem';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
const API = `${BACKEND_URL}/api`;

export const MessagingHub = ({ user }) => {
  const [activeJobs, setActiveJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchActiveJobs();
  }, [user]);

  const fetchActiveJobs = async () => {
    try {
      const response = await axios.get(`${API}/jobs`);
      // Filter jobs where the current user is involved and it's not simply 'open' or 'draft'
      const relevantJobs = response.data.filter(job => 
        ['assigned', 'in_progress', 'completed'].includes(job.status)
      );
      setActiveJobs(relevantJobs);
      
      if (relevantJobs.length > 0 && !selectedJob) {
        setSelectedJob(relevantJobs[0]);
      }
    } catch (error) {
      toast.error('Failed to load active conversations');
    } finally {
      setLoading(false);
    }
  };

  const getOpponent = (job) => {
    // For a real platform, we'd fetch the exact user details.
    // For demo purposes, we'll label it based on the current user's role.
    const isCustomer = user?.role === 'customer';
    return {
      name: isCustomer ? 'Assigned Worker' : 'Customer (Client)',
      phone: '9876543210' // Masked automatically by ChatSystem
    };
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto flex h-[80vh] border rounded-lg overflow-hidden bg-white shadow-sm mt-4">
      {/* Inbox Pane */}
      <div className="w-1/3 border-r bg-gray-50 flex flex-col">
        <div className="p-4 border-b bg-white">
          <h2 className="text-xl font-bold flex items-center">
            <MessageCircle className="w-5 h-5 mr-2" />
            Messages
          </h2>
        </div>
        
        <div className="flex-1 overflow-y-auto">
          {activeJobs.length === 0 ? (
            <div className="p-8 text-center text-gray-500 text-sm">
              <Briefcase className="w-8 h-8 mx-auto mb-2 opacity-50" />
              You have no active conversations. Secure a job application to start chatting!
            </div>
          ) : (
            activeJobs.map(job => (
              <div 
                key={job.id}
                onClick={() => setSelectedJob(job)}
                className={`p-4 border-b cursor-pointer transition-colors ${
                  selectedJob?.id === job.id ? 'bg-orange-50 border-orange-200' : 'hover:bg-gray-100 bg-white'
                }`}
              >
                <div className="flex justify-between items-start mb-1">
                  <h3 className="font-semibold text-gray-900 truncate pr-4">{job.title}</h3>
                  <span className="text-xs px-2 py-1 bg-gray-100 rounded-full">{job.status}</span>
                </div>
                <p className="text-sm text-gray-600 truncate">{getOpponent(job).name}</p>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Chat Pane */}
      <div className="w-2/3 flex flex-col bg-white overflow-hidden">
        {selectedJob ? (
          <div className="flex-1 overflow-hidden p-4">
            <h3 className="text-sm font-semibold text-gray-500 mb-2 uppercase tracking-wide">
              Regarding: {selectedJob.title}
            </h3>
            <ChatSystem 
              jobId={selectedJob.id} 
              currentUser={user} 
              otherUser={getOpponent(selectedJob)}
            />
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-gray-400">
            <MessageCircle className="w-16 h-16 mb-4 opacity-20" />
            <p>Select an ongoing job conversation to view messages</p>
          </div>
        )}
      </div>
    </div>
  );
};

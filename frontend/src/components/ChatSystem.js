import React, { useState, useEffect, useRef } from 'react';
import { Send, Phone, Shield, AlertCircle, CheckCircle2, Clock } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';
import { API, getErrorMessage } from '../lib/api';

export const ChatSystem = ({ jobId, currentUser, otherUser }) => {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef(null);
  const chatContainerRef = useRef(null);

  useEffect(() => {
    fetchMessages();
    // Set up polling for new messages (in production, use WebSocket)
    const interval = setInterval(fetchMessages, 3000);
    return () => clearInterval(interval);
  }, [jobId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const fetchMessages = async () => {
    try {
      const response = await axios.get(`${API}/jobs/${jobId}/messages`);
      setMessages(response.data);
    } catch (error) {
      if (loading) {
        toast.error('Failed to load messages');
      }
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!newMessage.trim()) return;

    setSending(true);
    try {
      await axios.post(`${API}/jobs/${jobId}/messages`, {
        content: newMessage,
        message_type: 'text'
      });
      
      setNewMessage('');
      fetchMessages();
    } catch (error) {
      toast.error(getErrorMessage(error, 'Failed to send message'));
    } finally {
      setSending(false);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const formatDate = (timestamp) => {
    const date = new Date(timestamp);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(today.getDate() - 1);

    if (date.toDateString() === today.toDateString()) {
      return 'Today';
    } else if (date.toDateString() === yesterday.toDateString()) {
      return 'Yesterday';
    } else {
      return date.toLocaleDateString();
    }
  };

  const groupMessagesByDate = (messages) => {
    const groups = {};
    messages.forEach(message => {
      const date = new Date(message.created_at).toDateString();
      if (!groups[date]) {
        groups[date] = [];
      }
      groups[date].push(message);
    });
    return groups;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-600"></div>
      </div>
    );
  }

  const messageGroups = groupMessagesByDate(messages);

  return (
    <div className="flex flex-col h-96 bg-white rounded-lg border">
      {/* Chat Header */}
      <div className="flex items-center justify-between p-4 border-b bg-gray-50 rounded-t-lg">
        <div className="flex items-center">
          <div className="w-10 h-10 bg-orange-100 rounded-full flex items-center justify-center">
            <span className="text-orange-600 font-semibold">
              {otherUser?.name?.charAt(0) || '?'}
            </span>
          </div>
          <div className="ml-3">
            <h4 className="font-medium text-gray-900">{otherUser?.name || 'User'}</h4>
            <div className="flex items-center text-sm text-gray-500">
              <Shield className="w-4 h-4 mr-1" />
              Phone numbers are masked for privacy
            </div>
          </div>
        </div>
        <div className="text-right text-sm text-gray-500">
          <div className="flex items-center">
            <Phone className="w-4 h-4 mr-1" />
            {otherUser?.phone ? otherUser.phone.replace(/(\d{2})\d{6}(\d{2})/, '$1****$2') : 'Number hidden'}
          </div>
        </div>
      </div>

      {/* Messages */}
      <div 
        ref={chatContainerRef}
        className="flex-1 overflow-y-auto p-4 space-y-4"
        style={{ maxHeight: '300px' }}
      >
        {Object.keys(messageGroups).length > 0 ? (
          Object.entries(messageGroups).map(([date, dayMessages]) => (
            <div key={date}>
              {/* Date Separator */}
              <div className="flex items-center justify-center my-4">
                <div className="bg-gray-100 px-3 py-1 rounded-full text-xs text-gray-600">
                  {formatDate(date)}
                </div>
              </div>
              
              {/* Messages for this date */}
              {dayMessages.map((message) => {
                const isOwnMessage = message.sender_user_id === currentUser.id;
                return (
                  <div
                    key={message.id}
                    className={`flex ${isOwnMessage ? 'justify-end' : 'justify-start'} mb-2`}
                  >
                    <div
                      className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                        isOwnMessage
                          ? 'bg-orange-600 text-white'
                          : 'bg-gray-100 text-gray-900'
                      }`}
                    >
                      {message.message_type === 'system' ? (
                        <div className="flex items-center text-sm">
                          <AlertCircle className="w-4 h-4 mr-2" />
                          {message.content}
                        </div>
                      ) : (
                        <div>
                          <p className="text-sm">{message.content}</p>
                          <div className={`flex items-center justify-end mt-1 text-xs ${
                            isOwnMessage ? 'text-orange-200' : 'text-gray-500'
                          }`}>
                            <Clock className="w-3 h-3 mr-1" />
                            {formatTime(message.created_at)}
                            {isOwnMessage && (
                              <CheckCircle2 className={`w-3 h-3 ml-1 ${
                                message.is_read ? 'text-green-300' : 'text-orange-200'
                              }`} />
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          ))
        ) : (
          <div className="text-center text-gray-500 py-8">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Send className="w-8 h-8 text-gray-400" />
            </div>
            <p>No messages yet. Start the conversation!</p>
            <div className="mt-2 text-sm bg-blue-50 text-blue-700 p-3 rounded-lg inline-block">
              <Shield className="w-4 h-4 inline mr-2" />
              Your phone numbers are automatically masked for privacy
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Message Input */}
      <div className="border-t p-4">
        <form onSubmit={sendMessage} className="flex space-x-2">
          <input
            type="text"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            placeholder="Type your message..."
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-orange-500 focus:border-orange-500"
            disabled={sending}
          />
          <button
            type="submit"
            disabled={sending || !newMessage.trim()}
            className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:opacity-50 transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
        <div className="mt-2 text-xs text-gray-500 text-center">
          <Shield className="w-3 h-3 inline mr-1" />
          Messages are monitored for safety. Phone numbers shared will be automatically masked.
        </div>
      </div>
    </div>
  );
};
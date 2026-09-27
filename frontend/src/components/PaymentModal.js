import React, { useState, useEffect } from 'react';
import { useRazorpay } from 'react-razorpay';
import { X, CreditCard, Smartphone, Banknote, CheckCircle } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';
import { API, getErrorMessage } from '../lib/api';

export const PaymentModal = ({ isOpen, onClose, job, amount, onSuccess }) => {
  // react-razorpay v3 returns an object (v2 returned an array)
  const { Razorpay } = useRazorpay();
  const [selectedMethod, setSelectedMethod] = useState('cod');
  const [loading, setLoading] = useState(false);
  const [onlineEnabled, setOnlineEnabled] = useState(false);

  // Online methods are only offered when the backend has a payment gateway configured
  useEffect(() => {
    if (!isOpen) return;
    axios.get(`${API}/config`)
      .then((response) => setOnlineEnabled(Boolean(response.data?.razorpay_key_id)))
      .catch(() => setOnlineEnabled(false));
  }, [isOpen]);

  const paymentMethods = [
    {
      id: 'cod',
      name: 'Cash on Delivery (COD)',
      icon: Banknote,
      description: 'Pay the worker in cash for the completed work',
      enabled: true
    },
    {
      id: 'upi',
      name: 'UPI Payment',
      icon: Smartphone,
      description: onlineEnabled ? 'Pay instantly via UPI (Google Pay, PhonePe, etc.)' : 'Not available yet',
      enabled: onlineEnabled
    },
    {
      id: 'card',
      name: 'Credit/Debit Card',
      icon: CreditCard,
      description: onlineEnabled ? 'Pay securely with your card' : 'Not available yet',
      enabled: onlineEnabled
    }
  ];

  const handlePayment = async () => {
    setLoading(true);

    try {
      // The server charges the amount agreed at assignment; we send it only as a check
      const response = await axios.post(`${API}/payments/create-order`, {
        job_id: job.id,
        amount,
        method: selectedMethod
      });

      if (selectedMethod === 'cod') {
        toast.success('Cash payment recorded. The job is now complete!');
        onSuccess();
        onClose();
        return;
      }

      if (!Razorpay) {
        toast.error('Payment gateway failed to load. Please try again.');
        return;
      }

      const { razorpay_order_id, key_id, payment_id } = response.data;
      const options = {
        key: key_id,
        amount: response.data.amount,
        currency: 'INR',
        order_id: razorpay_order_id,
        name: 'Sanyuth',
        description: `Payment for ${job.title}`,
        handler: async (razorpayResponse) => {
          try {
            await axios.post(`${API}/payments/verify`, {
              payment_id,
              razorpay_payment_id: razorpayResponse.razorpay_payment_id,
              razorpay_signature: razorpayResponse.razorpay_signature
            });

            toast.success('Payment completed successfully!');
            onSuccess();
            onClose();
          } catch (error) {
            toast.error(getErrorMessage(error, 'Payment verification failed'));
          }
        },
        theme: {
          color: '#ea580c'
        }
      };

      const razorpayInstance = new Razorpay(options);
      razorpayInstance.open();
    } catch (error) {
      toast.error(getErrorMessage(error, 'Payment failed'));
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl max-w-md w-full p-6">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-bold text-gray-900">Complete Job & Pay</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Job Summary */}
        <div className="bg-gray-50 rounded-lg p-4 mb-6">
          <h4 className="font-semibold text-gray-900 mb-2">{job.title}</h4>
          <div className="flex justify-between text-sm text-gray-600">
            <span>Agreed Amount:</span>
            <span className="font-bold text-lg text-orange-600">₹{Number(amount || 0).toLocaleString()}</span>
          </div>
        </div>

        {/* Payment Methods */}
        <div className="space-y-3 mb-6">
          <h5 className="font-medium text-gray-900">Select Payment Method</h5>
          {paymentMethods.map((method) => (
            <div
              key={method.id}
              onClick={() => method.enabled && setSelectedMethod(method.id)}
              className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                selectedMethod === method.id
                  ? 'border-orange-500 bg-orange-50'
                  : 'border-gray-200 hover:border-orange-300'
              } ${!method.enabled ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <div className="flex items-center">
                <method.icon className={`w-6 h-6 mr-3 ${
                  selectedMethod === method.id ? 'text-orange-600' : 'text-gray-600'
                }`} />
                <div className="flex-1">
                  <h6 className="font-medium text-gray-900">{method.name}</h6>
                  <p className="text-sm text-gray-600">{method.description}</p>
                </div>
                {selectedMethod === method.id && (
                  <CheckCircle className="w-5 h-5 text-orange-600" />
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={handlePayment}
            disabled={loading || !amount}
            className="flex-1 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:opacity-50"
          >
            {loading ? 'Processing...' : `Pay ₹${Number(amount || 0).toLocaleString()}`}
          </button>
        </div>
      </div>
    </div>
  );
};

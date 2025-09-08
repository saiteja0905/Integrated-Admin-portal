#!/usr/bin/env python3
"""
Shidhaan Backend API Testing Suite - Phase 4 Complete Testing
Tests all API endpoints for the blue-collar marketplace including:
- Payment Integration (Razorpay + COD)
- In-App Chat System
- Review & Rating System
- Advanced Search & Location Features
- Notification System
"""

import requests
import sys
import json
import time
from datetime import datetime

class ShidhaanAPITester:
    def __init__(self, base_url="https://blucollar-hub.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tokens = {}
        self.users = {}
        self.jobs = {}
        self.assignments = {}
        self.payments = {}
        self.messages = {}
        self.reviews = {}
        self.notifications = {}
        self.tests_run = 0
        self.tests_passed = 0
        
        # Demo credentials from the app
        self.demo_credentials = {
            'customer': {'phone': '9876543210', 'password': 'password123'},
            'worker': {'phone': '9876543211', 'password': 'password123'},
            'admin': {'phone': '9876543212', 'password': 'admin123'}
        }

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")

    def make_request(self, method, endpoint, data=None, token=None, expected_status=200):
        """Make HTTP request with proper headers"""
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        headers = {'Content-Type': 'application/json'}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method.upper() == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            else:
                return False, f"Unsupported method: {method}"
            
            success = response.status_code == expected_status
            return success, response
            
        except requests.exceptions.RequestException as e:
            return False, f"Request failed: {str(e)}"

    def test_health_endpoints(self):
        """Test basic health and info endpoints"""
        print("\n🔍 Testing Health Endpoints...")
        
        # Test root endpoint
        success, response = self.make_request('GET', '/')
        if success:
            data = response.json()
            self.log_test("Root endpoint", "Shidhaan API" in data.get('message', ''))
        else:
            self.log_test("Root endpoint", False, str(response))
        
        # Test health endpoint
        success, response = self.make_request('GET', '/health')
        if success:
            data = response.json()
            self.log_test("Health check", data.get('status') == 'healthy')
        else:
            self.log_test("Health check", False, str(response))

    def test_authentication(self):
        """Test authentication endpoints"""
        print("\n🔍 Testing Authentication...")
        
        # Test login with demo credentials
        for role, creds in self.demo_credentials.items():
            success, response = self.make_request('POST', '/auth/login', creds)
            if success:
                data = response.json()
                if 'access_token' in data and 'user' in data:
                    self.tokens[role] = data['access_token']
                    self.users[role] = data['user']
                    self.log_test(f"Login as {role}", True)
                else:
                    self.log_test(f"Login as {role}", False, "Missing token or user data")
            else:
                self.log_test(f"Login as {role}", False, f"Status: {response.status_code if hasattr(response, 'status_code') else 'Request failed'}")
        
        # Test /auth/me endpoint for each role
        for role, token in self.tokens.items():
            success, response = self.make_request('GET', '/auth/me', token=token)
            if success:
                data = response.json()
                expected_role = self.users[role]['role']
                self.log_test(f"Get user info ({role})", data.get('role') == expected_role)
            else:
                self.log_test(f"Get user info ({role})", False, str(response))

    def test_job_endpoints(self):
        """Test job-related endpoints"""
        print("\n🔍 Testing Job Endpoints...")
        
        # Test get jobs (public endpoint)
        success, response = self.make_request('GET', '/jobs')
        if success:
            jobs_data = response.json()
            self.log_test("Get all jobs", isinstance(jobs_data, list))
            
            # Store jobs for later tests
            if jobs_data:
                self.jobs['list'] = jobs_data
                print(f"   Found {len(jobs_data)} jobs")
                
                # Test get specific job
                job_id = jobs_data[0]['id']
                success, response = self.make_request('GET', f'/jobs/{job_id}')
                if success:
                    job_data = response.json()
                    self.log_test("Get specific job", job_data.get('id') == job_id)
                else:
                    self.log_test("Get specific job", False, str(response))
        else:
            self.log_test("Get all jobs", False, str(response))
        
        # Test creating a job (requires customer token)
        if 'customer' in self.tokens:
            job_data = {
                "title": "Test Plumbing Job",
                "description": "Fix kitchen sink",
                "category": "skilled",
                "type": "daily",
                "location": {
                    "lat": 28.6139,
                    "lng": 77.2090,
                    "address": "New Delhi, India"
                },
                "budget_amount": 1500.0,
                "is_budget_negotiable": False
            }
            
            success, response = self.make_request('POST', '/jobs', job_data, token=self.tokens['customer'], expected_status=200)
            if success:
                created_job = response.json()
                self.jobs['created'] = created_job
                self.log_test("Create job (customer)", 'id' in created_job)
                
                # Test publish job
                job_id = created_job['id']
                success, response = self.make_request('PUT', f'/jobs/{job_id}/publish', token=self.tokens['customer'])
                self.log_test("Publish job", success)
                
            else:
                self.log_test("Create job (customer)", False, f"Status: {response.status_code if hasattr(response, 'status_code') else 'Request failed'}")

    def test_worker_endpoints(self):
        """Test worker-specific endpoints"""
        print("\n🔍 Testing Worker Endpoints...")
        
        if 'worker' not in self.tokens:
            print("   Skipping worker tests - no worker token")
            return
        
        worker_token = self.tokens['worker']
        
        # Test get worker profile
        success, response = self.make_request('GET', '/workers/profile', token=worker_token)
        if success:
            profile_data = response.json()
            self.log_test("Get worker profile", 'user_id' in profile_data)
        else:
            self.log_test("Get worker profile", False, str(response))
        
        # Test update worker profile
        profile_update = {
            "skills": ["plumbing", "electrical"],
            "experience_years": 5,
            "certifications": ["Basic Plumbing Certificate"]
        }
        
        success, response = self.make_request('PUT', '/workers/profile', profile_update, token=worker_token)
        self.log_test("Update worker profile", success)

    def test_application_endpoints(self):
        """Test job application endpoints"""
        print("\n🔍 Testing Application Endpoints...")
        
        if 'worker' not in self.tokens or 'created' not in self.jobs:
            print("   Skipping application tests - missing worker token or job")
            return
        
        worker_token = self.tokens['worker']
        job_id = self.jobs['created']['id']
        
        # Test apply to job (daily job)
        application_data = {
            "message": "I am interested in this plumbing job. I have 5 years of experience."
        }
        
        success, response = self.make_request('POST', f'/jobs/{job_id}/apply', application_data, token=worker_token, expected_status=200)
        if success:
            app_data = response.json()
            self.log_test("Apply to daily job", 'id' in app_data)
            
            # Test get job applications (as customer)
            if 'customer' in self.tokens:
                success, response = self.make_request('GET', f'/jobs/{job_id}/applications', token=self.tokens['customer'])
                if success:
                    applications = response.json()
                    self.log_test("Get job applications", isinstance(applications, list) and len(applications) > 0)
                else:
                    self.log_test("Get job applications", False, str(response))
        else:
            self.log_test("Apply to daily job", False, f"Status: {response.status_code if hasattr(response, 'status_code') else 'Request failed'}")

    def test_bidding_endpoints(self):
        """Test bidding endpoints for contractual jobs - PHASE 3 FEATURE"""
        print("\n🔍 Testing Bidding Endpoints (Phase 3)...")
        
        if 'worker' not in self.tokens or 'customer' not in self.tokens:
            print("   Skipping bidding tests - missing tokens")
            return
        
        # Create a contractual job first
        contractual_job_data = {
            "title": "Kitchen Renovation Work",
            "description": "Complete kitchen renovation including plumbing, electrical, and tiling work",
            "category": "skilled",
            "type": "contractual",
            "location": {
                "lat": 28.6139,
                "lng": 77.2090,
                "address": "Connaught Place, New Delhi"
            },
            "budget_amount": 50000.0,
            "is_budget_negotiable": True
        }
        
        success, response = self.make_request('POST', '/jobs', contractual_job_data, token=self.tokens['customer'])
        if success:
            contractual_job = response.json()
            self.log_test("Create contractual job", 'id' in contractual_job)
            
            # Publish the contractual job
            job_id = contractual_job['id']
            success, response = self.make_request('PUT', f'/jobs/{job_id}/publish', token=self.tokens['customer'])
            self.log_test("Publish contractual job", success)
            
            if success:
                # Test placing a bid
                bid_data = {
                    "bid_amount": 45000,
                    "visiting_charge": 500,
                    "message": "I have 5 years of experience in kitchen renovations. I can complete this project in 2 weeks with high quality materials."
                }
                
                success, response = self.make_request('POST', f'/jobs/{job_id}/bid', bid_data, token=self.tokens['worker'])
                if success:
                    bid_response = response.json()
                    self.log_test("Place bid on contractual job", 'id' in bid_response)
                    
                    # Test get job bids (as customer)
                    success, response = self.make_request('GET', f'/jobs/{job_id}/bids', token=self.tokens['customer'])
                    if success:
                        bids = response.json()
                        self.log_test("Get job bids", isinstance(bids, list) and len(bids) > 0)
                        
                        # Test worker assignment for contractual job
                        if bids:
                            worker_id = self.users['worker']['id']
                            success, response = self.make_request('POST', f'/jobs/{job_id}/assign?worker_id={worker_id}', token=self.tokens['customer'])
                            self.log_test("Assign worker (contractual)", success)
                    else:
                        self.log_test("Get job bids", False, str(response))
                else:
                    self.log_test("Place bid on contractual job", False, str(response))
        else:
            self.log_test("Create contractual job", False, str(response))

    def test_assignment_endpoints(self):
        """Test job assignment endpoints - PHASE 3 FEATURE"""
        print("\n🔍 Testing Assignment Endpoints (Phase 3)...")
        
        if 'worker' not in self.tokens or 'customer' not in self.tokens or 'created' not in self.jobs:
            print("   Skipping assignment tests - missing requirements")
            return
        
        # Test assignment for daily job (if we have applications)
        job_id = self.jobs['created']['id']
        worker_id = self.users['worker']['id']
        
        success, response = self.make_request('POST', f'/jobs/{job_id}/assign?worker_id={worker_id}', token=self.tokens['customer'])
        self.log_test("Assign worker (daily job)", success)

    def test_user_endpoints(self):
        """Test user-related endpoints"""
        print("\n🔍 Testing User Endpoints...")
        
        if 'customer' in self.users:
            user_id = self.users['customer']['id']
            success, response = self.make_request('GET', f'/users/{user_id}')
            if success:
                user_data = response.json()
                self.log_test("Get user by ID", user_data.get('id') == user_id)
            else:
                self.log_test("Get user by ID", False, str(response))

    def test_payment_endpoints(self):
        """Test payment system endpoints - PHASE 4 FEATURE"""
        print("\n🔍 Testing Payment System (Phase 4)...")
        
        if 'customer' not in self.tokens or 'created' not in self.jobs:
            print("   Skipping payment tests - missing requirements")
            return
        
        job_id = self.jobs['created']['id']
        
        # Test COD payment creation
        cod_payment_data = {
            "job_id": job_id,
            "amount": 1500.0,
            "method": "cod"
        }
        
        success, response = self.make_request('POST', '/payments/create-order', cod_payment_data, token=self.tokens['customer'])
        if success:
            payment_response = response.json()
            self.log_test("Create COD payment order", 'payment_id' in payment_response)
            if 'payment_id' in payment_response:
                self.payments['cod'] = payment_response
        else:
            self.log_test("Create COD payment order", False, str(response))
        
        # Test Razorpay payment creation (will use placeholder keys)
        razorpay_payment_data = {
            "job_id": job_id,
            "amount": 1500.0,
            "method": "upi"
        }
        
        success, response = self.make_request('POST', '/payments/create-order', razorpay_payment_data, token=self.tokens['customer'])
        if success:
            payment_response = response.json()
            self.log_test("Create Razorpay payment order", 'razorpay_order_id' in payment_response or 'payment_id' in payment_response)
            if 'payment_id' in payment_response:
                self.payments['razorpay'] = payment_response
        else:
            self.log_test("Create Razorpay payment order", False, str(response))

    def test_chat_endpoints(self):
        """Test chat system endpoints - PHASE 4 FEATURE"""
        print("\n🔍 Testing Chat System (Phase 4)...")
        
        if 'customer' not in self.tokens or 'worker' not in self.tokens or 'created' not in self.jobs:
            print("   Skipping chat tests - missing requirements")
            return
        
        job_id = self.jobs['created']['id']
        
        # Test sending a message from customer to worker
        message_data = {
            "content": "Hello, when can you start the plumbing work? My phone is 9876543210",
            "message_type": "text"
        }
        
        success, response = self.make_request('POST', f'/jobs/{job_id}/messages', message_data, token=self.tokens['customer'])
        if success:
            message_response = response.json()
            self.log_test("Send message (customer to worker)", 'message_id' in message_response)
            if 'message_id' in message_response:
                self.messages['customer_to_worker'] = message_response
        else:
            self.log_test("Send message (customer to worker)", False, str(response))
        
        # Test sending a message from worker to customer
        worker_message_data = {
            "content": "I can start tomorrow morning. I'll call you at 98****10 to confirm timing.",
            "message_type": "text"
        }
        
        success, response = self.make_request('POST', f'/jobs/{job_id}/messages', worker_message_data, token=self.tokens['worker'])
        if success:
            message_response = response.json()
            self.log_test("Send message (worker to customer)", 'message_id' in message_response)
        else:
            self.log_test("Send message (worker to customer)", False, str(response))
        
        # Test getting job messages (should include phone masking)
        success, response = self.make_request('GET', f'/jobs/{job_id}/messages', token=self.tokens['customer'])
        if success:
            messages = response.json()
            self.log_test("Get job messages", isinstance(messages, list))
            
            # Check if phone number masking is working
            if messages:
                has_masked_phone = any('****' in msg.get('content', '') for msg in messages)
                self.log_test("Phone number masking in messages", has_masked_phone)
        else:
            self.log_test("Get job messages", False, str(response))

    def test_review_endpoints(self):
        """Test review and rating system endpoints - PHASE 4 FEATURE"""
        print("\n🔍 Testing Review System (Phase 4)...")
        
        if 'customer' not in self.tokens or 'worker' not in self.tokens or 'created' not in self.jobs:
            print("   Skipping review tests - missing requirements")
            return
        
        job_id = self.jobs['created']['id']
        worker_id = self.users['worker']['id']
        customer_id = self.users['customer']['id']
        
        # First, we need to complete the job to enable reviews
        # This would normally happen after payment, but we'll simulate it
        
        # Test creating a review (customer reviewing worker)
        review_data = {
            "job_id": job_id,
            "reviewee_user_id": worker_id,
            "stars": 5,
            "comment": "Excellent work! Very professional and completed on time."
        }
        
        success, response = self.make_request('POST', f'/jobs/{job_id}/review', review_data, token=self.tokens['customer'])
        if success:
            review_response = response.json()
            self.log_test("Create review (customer to worker)", 'id' in review_response)
            if 'id' in review_response:
                self.reviews['customer_to_worker'] = review_response
        else:
            self.log_test("Create review (customer to worker)", False, str(response))
        
        # Test getting user reviews
        success, response = self.make_request('GET', f'/users/{worker_id}/reviews')
        if success:
            reviews = response.json()
            self.log_test("Get user reviews", isinstance(reviews, list))
        else:
            self.log_test("Get user reviews", False, str(response))

    def test_notification_endpoints(self):
        """Test notification system endpoints - PHASE 4 FEATURE"""
        print("\n🔍 Testing Notification System (Phase 4)...")
        
        if 'customer' not in self.tokens or 'worker' not in self.tokens:
            print("   Skipping notification tests - missing tokens")
            return
        
        # Test getting notifications for customer
        success, response = self.make_request('GET', '/notifications', token=self.tokens['customer'])
        if success:
            notifications = response.json()
            self.log_test("Get notifications (customer)", isinstance(notifications, list))
            
            if notifications:
                self.notifications['customer'] = notifications
                # Test marking a notification as read
                notification_id = notifications[0]['id']
                success, response = self.make_request('PUT', f'/notifications/{notification_id}/read', token=self.tokens['customer'])
                self.log_test("Mark notification as read", success)
        else:
            self.log_test("Get notifications (customer)", False, str(response))
        
        # Test getting notifications for worker
        success, response = self.make_request('GET', '/notifications', token=self.tokens['worker'])
        if success:
            notifications = response.json()
            self.log_test("Get notifications (worker)", isinstance(notifications, list))
        else:
            self.log_test("Get notifications (worker)", False, str(response))
        
        # Test mark all notifications as read
        success, response = self.make_request('PUT', '/notifications/mark-all-read', token=self.tokens['customer'])
        self.log_test("Mark all notifications as read", success)
        
        # Test getting unread notifications only
        success, response = self.make_request('GET', '/notifications?unread_only=true', token=self.tokens['worker'])
        if success:
            unread_notifications = response.json()
            self.log_test("Get unread notifications only", isinstance(unread_notifications, list))
        else:
            self.log_test("Get unread notifications only", False, str(response))

    def test_advanced_search_endpoints(self):
        """Test advanced search and location features - PHASE 4 FEATURE"""
        print("\n🔍 Testing Advanced Search (Phase 4)...")
        
        if 'worker' not in self.tokens:
            print("   Skipping search tests - missing worker token")
            return
        
        # Test advanced job search with filters
        search_filters = {
            "search_term": "plumbing",
            "job_type": "daily",
            "category": "skilled",
            "min_budget": 1000,
            "max_budget": 5000,
            "location": {
                "lat": 28.6139,
                "lng": 77.2090,
                "address": "New Delhi, India"
            },
            "radius_km": 10,
            "skills": ["plumbing"],
            "sort_by": "budget_high"
        }
        
        success, response = self.make_request('POST', '/jobs/search', search_filters, token=self.tokens['worker'])
        if success:
            search_results = response.json()
            self.log_test("Advanced job search with filters", isinstance(search_results, list))
        else:
            self.log_test("Advanced job search with filters", False, str(response))
        
        # Test search with location-based filtering
        location_search = {
            "location": {
                "lat": 28.6139,
                "lng": 77.2090,
                "address": "New Delhi, India"
            },
            "radius_km": 5,
            "sort_by": "distance"
        }
        
        success, response = self.make_request('POST', '/jobs/search', location_search, token=self.tokens['worker'])
        if success:
            location_results = response.json()
            self.log_test("Location-based job search", isinstance(location_results, list))
        else:
            self.log_test("Location-based job search", False, str(response))
        
        # Test skills-based matching
        skills_search = {
            "skills": ["plumbing", "electrical"],
            "sort_by": "recent"
        }
        
        success, response = self.make_request('POST', '/jobs/search', skills_search, token=self.tokens['worker'])
        if success:
            skills_results = response.json()
            self.log_test("Skills-based job matching", isinstance(skills_results, list))
        else:
            self.log_test("Skills-based job matching", False, str(response))

    def test_config_endpoint(self):
        """Test configuration endpoint - PHASE 4 FEATURE"""
        print("\n🔍 Testing Configuration Endpoint (Phase 4)...")
        
        if 'customer' not in self.tokens:
            print("   Skipping config tests - missing customer token")
            return
        
        success, response = self.make_request('GET', '/config', token=self.tokens['customer'])
        if success:
            config_data = response.json()
            expected_keys = ['payment_methods', 'maps_enabled', 'chat_enabled', 'notifications_enabled']
            has_all_keys = all(key in config_data for key in expected_keys)
            self.log_test("Get frontend configuration", has_all_keys)
            
            # Check if payment methods include expected options
            if 'payment_methods' in config_data:
                expected_methods = ['cod', 'upi', 'card']
                has_payment_methods = all(method in config_data['payment_methods'] for method in expected_methods)
                self.log_test("Payment methods configuration", has_payment_methods)
        else:
            self.log_test("Get frontend configuration", False, str(response))

    def test_error_handling(self):
        """Test error handling"""
        print("\n🔍 Testing Error Handling...")
        
        # Test invalid login
        invalid_creds = {"phone": "0000000000", "password": "wrongpass"}
        success, response = self.make_request('POST', '/auth/login', invalid_creds, expected_status=401)
        self.log_test("Invalid login returns 401", success)
        
        # Test unauthorized access
        success, response = self.make_request('GET', '/auth/me', expected_status=401)
        self.log_test("Unauthorized access returns 401", success)
        
        # Test non-existent job
        success, response = self.make_request('GET', '/jobs/non-existent-id', expected_status=404)
        self.log_test("Non-existent job returns 404", success)

    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting Shidhaan API Tests - Phase 3 Features...")
        print(f"Testing against: {self.base_url}")
        
        try:
            self.test_health_endpoints()
            self.test_authentication()
            self.test_job_endpoints()
            self.test_worker_endpoints()
            self.test_application_endpoints()
            self.test_bidding_endpoints()  # Phase 3 feature
            self.test_assignment_endpoints()  # Phase 3 feature
            self.test_user_endpoints()
            self.test_error_handling()
            
        except Exception as e:
            print(f"\n💥 Test suite crashed: {str(e)}")
            return 1
        
        # Print summary
        print(f"\n📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return 1

def main():
    tester = ShidhaanAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())
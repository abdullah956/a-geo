import api from './api';

class CourseService {
  // Get all courses (for admins)
  async getAllCourses() {
    try {
      const response = await api.get('/courses/');
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  }

  // Get teacher's courses
  async getTeacherCourses() {
    try {
      const response = await api.get('/courses/teacher/courses/');
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  }

  // Create a new course (admin only)
  async createCourse(courseData) {
    try {
      const response = await api.post('/courses/create/', courseData);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  }

  // Update a course (admin only)
  async updateCourse(courseId, courseData) {
    try {
      const response = await api.put(`/courses/${courseId}/update/`, courseData);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  }

  // Delete a course (admin only)
  async deleteCourse(courseId) {
    try {
      await api.delete(`/courses/${courseId}/delete/`);
      return true;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  }

  // Get course details
  async getCourseDetails(courseId) {
    try {
      const response = await api.get(`/courses/${courseId}/`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  }

  // Enroll student in course (admin only)
  async enrollStudent(courseId, studentId) {
    try {
      const response = await api.post('/courses/enroll/', {
        course: courseId,
        student: studentId
      });
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  }

  // Get course enrollments
  async getCourseEnrollments(courseId) {
    try {
      const response = await api.get(`/courses/${courseId}/enrollments/`);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  }
}

export const courseService = new CourseService();

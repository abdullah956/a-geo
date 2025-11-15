import React, { useState, useEffect } from 'react';
import { courseService } from '../../services/courseService';
import './Dashboard.css';

const TeacherStudentsView = ({ onBack }) => {
  const [studentsData, setStudentsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedCourse, setSelectedCourse] = useState('all');

  useEffect(() => {
    fetchStudents();
  }, []);

  const fetchStudents = async () => {
    try {
      setLoading(true);
      const data = await courseService.getTeacherStudents();
      setStudentsData(data);
    } catch (error) {
      console.error('Error fetching students:', error);
      setError('Failed to load students');
    } finally {
      setLoading(false);
    }
  };

  const getUniqueCoursesFromStudents = () => {
    if (!studentsData?.students) return [];
    
    const coursesMap = new Map();
    studentsData.students.forEach(enrollment => {
      if (!coursesMap.has(enrollment.course)) {
        coursesMap.set(enrollment.course, {
          id: enrollment.course,
          code: enrollment.course_code,
          title: enrollment.course_title
        });
      }
    });
    
    return Array.from(coursesMap.values());
  };

  const getFilteredStudents = () => {
    if (!studentsData?.students) return [];
    
    if (selectedCourse === 'all') {
      return studentsData.students;
    }
    
    return studentsData.students.filter(enrollment => 
      enrollment.course.toString() === selectedCourse
    );
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  if (loading) {
    return (
      <div className="dashboard">
        <div className="dashboard-loading">Loading students...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard">
        <div className="error-message">
          <h3>Error</h3>
          <p>{error}</p>
          <button onClick={onBack} className="back-btn">← Back to Dashboard</button>
        </div>
      </div>
    );
  }

  const filteredStudents = getFilteredStudents();
  const courses = getUniqueCoursesFromStudents();

  return (
    <div className="dashboard teacher-theme">
      <header className="dashboard-header">
        <div className="user-info">
          <h1>My Students</h1>
          <p>View all students enrolled in your courses</p>
        </div>
        <button onClick={onBack} className="back-btn">
          ← Back to Dashboard
        </button>
      </header>

      <main className="dashboard-main">
        <div className="students-management">
          <div className="students-header">
            <div className="students-stats">
              <div className="stat-card">
                <h3>{studentsData?.total_students || 0}</h3>
                <p>Total Students</p>
              </div>
              <div className="stat-card">
                <h3>{studentsData?.courses_count || 0}</h3>
                <p>Courses</p>
              </div>
              <div className="stat-card">
                <h3>{filteredStudents.length}</h3>
                <p>Filtered Students</p>
              </div>
            </div>

            <div className="filter-section">
              <label htmlFor="course-filter">Filter by Course:</label>
              <select 
                id="course-filter"
                value={selectedCourse} 
                onChange={(e) => setSelectedCourse(e.target.value)}
                className="course-filter-select"
              >
                <option value="all">All Courses</option>
                {courses.map(course => (
                  <option key={course.id} value={course.id.toString()}>
                    {course.code} - {course.title}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {filteredStudents.length > 0 ? (
            <div className="students-table-container">
              <table className="students-table">
                <thead>
                  <tr>
                    <th>Student Name</th>
                    <th>Email</th>
                    <th>Course</th>
                    <th>Enrolled Date</th>
                    <th>Attendance Rate</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredStudents.map((enrollment) => (
                    <tr key={`${enrollment.student}-${enrollment.course}`}>
                      <td className="student-name">
                        <div className="student-info">
                          <strong>{enrollment.student_name}</strong>
                        </div>
                      </td>
                      <td className="student-email">
                        {enrollment.student_email || 'N/A'}
                      </td>
                      <td className="course-info">
                        <div className="course-details">
                          <strong>{enrollment.course_code}</strong>
                          <span className="course-title">{enrollment.course_title}</span>
                        </div>
                      </td>
                      <td className="enrolled-date">
                        {formatDate(enrollment.enrolled_at)}
                      </td>
                      <td className="attendance-rate">
                        {enrollment.attendance_rate && enrollment.attendance_rate.display ? (
                          <span 
                            className="attendance-rate-badge"
                            style={{
                              color: enrollment.attendance_rate.percentage >= 80 ? '#10b981' : 
                                     enrollment.attendance_rate.percentage >= 60 ? '#f59e0b' : '#ef4444',
                              fontWeight: '600'
                            }}
                          >
                            {enrollment.attendance_rate.display}
                          </span>
                        ) : (
                          <span style={{ color: '#6b7280' }}>N/A</span>
                        )}
                      </td>
                      <td className="status">
                        <span className={`status-badge ${enrollment.is_active ? 'active' : 'inactive'}`}>
                          {enrollment.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="no-students-message">
              <h3>No Students Found</h3>
              <p>
                {selectedCourse === 'all' 
                  ? "You don't have any students enrolled in your courses yet."
                  : "No students found for the selected course."
                }
              </p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default TeacherStudentsView;

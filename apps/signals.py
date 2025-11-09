# """
# Django signal handlers for Learning Cloud API.
# Handles automatic functionality triggered by model events.
# """
# from django.db.models.signals import post_save, pre_save, post_delete
# from django.dispatch import receiver
# from django.utils import timezone
# from django.core.cache import cache
# import logging

# from apps.accounts.models import User
# from apps.content.models import Lesson, Subject
# from apps.quizzes.models import Quiz, QuizAttempt, QuizResult
# from apps.progress.models import (
#     StudentProgress, LearningStreak, SubjectProgress, 
#     GradeProgress, ProgressMilestone
# )
# from apps.analytics.models import Analytics
# from apps.notifications.models import Notification, NotificationPreference
# from apps.tasks import (
#     send_notification_email, update_learning_streaks, 
#     check_and_create_milestones, update_quiz_analytics,
#     update_subject_progress, update_grade_progress
# )

# logger = logging.getLogger(__name__)


# @receiver(post_save, sender=User)
# def create_user_notification_preferences(sender, instance, created, **kwargs):
#     """Create notification preferences when a new user is created"""
#     if created:
#         NotificationPreference.objects.get_or_create(user=instance)
#         logger.info(f"Created notification preferences for user {instance.username}")


# @receiver(post_save, sender=StudentProgress)
# def handle_lesson_progress_update(sender, instance, created, **kwargs):
#     """Handle lesson progress updates"""
#     if instance.status == 'COMPLETED':
#         # Update learning streak
#         update_learning_streaks.delay()
        
#         # Check for milestones
#         check_and_create_milestones.delay()
        
#         # Update subject progress
#         update_subject_progress.delay()
        
#         # Update grade progress
#         update_grade_progress.delay()
        
#         # Create analytics record
#         Analytics.objects.create(
#             student=instance.student,
#             lesson=instance.lesson,
#             metric_type='lesson_completion',
#             metric_value=1,
#             metadata={
#                 'lesson_title': instance.lesson.title,
#                 'subject': instance.lesson.chapter.subject.name,
#                 'grade_level': instance.lesson.chapter.subject.grade_level,
#                 'score': instance.score,
#                 'time_spent': instance.time_spent
#             }
#         )
        
#         # Send notification
#         if instance.score and instance.score >= 80:
#             notification = Notification.objects.create(
#                 user=instance.student,
#                 title="Great job!",
#                 message=f"You completed {instance.lesson.title} with a score of {instance.score}%!",
#                 notification_type='LESSON_COMPLETED',
#                 priority='MEDIUM',
#                 data={
#                     'lesson_id': instance.lesson.id,
#                     'score': instance.score
#                 }
#             )
            
#             # Send email notification
#             send_notification_email.delay(instance.student.id, notification.id)
        
#         logger.info(f"Lesson progress updated: {instance.student.username} - {instance.lesson.title}")


# @receiver(post_save, sender=QuizAttempt)
# def handle_quiz_attempt_completion(sender, instance, created, **kwargs):
#     """Handle quiz attempt completion"""
#     if instance.completed_at and not created:
#         # Update quiz analytics
#         update_quiz_analytics.delay()
        
#         # Create analytics record
#         Analytics.objects.create(
#             student=instance.student,
#             quiz=instance.quiz,
#             metric_type='quiz_completion',
#             metric_value=instance.score or 0,
#             metadata={
#                 'quiz_title': instance.quiz.title,
#                 'subject': instance.quiz.subject.name,
#                 'grade_level': instance.quiz.grade_level,
#                 'score': instance.score,
#                 'is_passed': instance.is_passed,
#                 'time_spent': instance.time_spent
#             }
#         )
        
#         # Send notification
#         if instance.is_passed:
#             notification = Notification.objects.create(
#                 user=instance.student,
#                 title="Quiz Passed!",
#                 message=f"Congratulations! You passed {instance.quiz.title} with a score of {instance.score}%!",
#                 notification_type='QUIZ_RESULT',
#                 priority='HIGH',
#                 data={
#                     'quiz_id': instance.quiz.id,
#                     'score': instance.score,
#                     'is_passed': True
#                 }
#             )
#         else:
#             notification = Notification.objects.create(
#                 user=instance.student,
#                 title="Quiz Results",
#                 message=f"You scored {instance.score}% on {instance.quiz.title}. Keep practicing!",
#                 notification_type='QUIZ_RESULT',
#                 priority='MEDIUM',
#                 data={
#                     'quiz_id': instance.quiz.id,
#                     'score': instance.score,
#                     'is_passed': False
#                 }
#             )
        
#         # Send email notification
#         send_notification_email.delay(instance.student.id, notification.id)
        
#         logger.info(f"Quiz attempt completed: {instance.student.username} - {instance.quiz.title}")


# @receiver(post_save, sender=ProgressMilestone)
# def handle_milestone_achievement(sender, instance, created, **kwargs):
#     """Handle milestone achievement"""
#     if created:
#         # Create analytics record
#         Analytics.objects.create(
#             student=instance.student,
#             metric_type='achievement_unlocked',
#             metric_value=1,
#             metadata={
#                 'milestone_type': instance.milestone_type,
#                 'title': instance.title,
#                 'description': instance.description
#             }
#         )
        
#         # Send notification
#         notification = Notification.objects.create(
#             user=instance.student,
#             title="Achievement Unlocked!",
#             message=f"Congratulations! You earned the {instance.title} achievement!",
#             notification_type='ACHIEVEMENT',
#             priority='HIGH',
#             data={
#                 'milestone_id': instance.id,
#                 'milestone_type': instance.milestone_type,
#                 'title': instance.title
#             }
#         )
        
#         # Send email notification
#         send_notification_email.delay(instance.student.id, notification.id)
        
#         logger.info(f"Milestone achieved: {instance.student.username} - {instance.title}")


# @receiver(post_save, sender=User)
# def handle_user_login(sender, instance, created, **kwargs):
#     """Handle user login (when last_login is updated)"""
#     if not created and instance.last_login:
#         # Create analytics record
#         Analytics.objects.create(
#             student=instance if instance.is_student() else None,
#             teacher=instance if instance.is_teacher() else None,
#             parent=instance if instance.is_parent() else None,
#             metric_type='login_activity',
#             metric_value=1,
#             metadata={
#                 'user_role': instance.role,
#                 'login_time': instance.last_login.isoformat()
#             }
#         )
        
#         # Update learning streak for students
#         if instance.is_student():
#             update_learning_streaks.delay()
        
#         logger.info(f"User login recorded: {instance.username}")


# @receiver(post_save, sender=Lesson)
# def handle_lesson_creation(sender, instance, created, **kwargs):
#     """Handle lesson creation"""
#     if created:
#         # Create analytics record
#         Analytics.objects.create(
#             teacher=instance.chapter.subject.created_by if hasattr(instance.chapter.subject, 'created_by') else None,
#             lesson=instance,
#             metric_type='content_created',
#             metric_value=1,
#             metadata={
#                 'lesson_title': instance.title,
#                 'content_type': instance.content_type,
#                 'subject': instance.chapter.subject.name,
#                 'grade_level': instance.chapter.subject.grade_level
#             }
#         )
        
#         logger.info(f"Lesson created: {instance.title}")


# @receiver(post_save, sender=Quiz)
# def handle_quiz_creation(sender, instance, created, **kwargs):
#     """Handle quiz creation"""
#     if created:
#         # Create analytics record
#         Analytics.objects.create(
#             teacher=instance.created_by,
#             quiz=instance,
#             metric_type='content_created',
#             metric_value=1,
#             metadata={
#                 'quiz_title': instance.title,
#                 'subject': instance.subject.name,
#                 'grade_level': instance.grade_level,
#                 'question_count': instance.questions.count()
#             }
#         )
        
#         logger.info(f"Quiz created: {instance.title}")


# @receiver(post_save, sender=Subject)
# def handle_subject_creation(sender, instance, created, **kwargs):
#     """Handle subject creation"""
#     if created:
#         # Create analytics record
#         Analytics.objects.create(
#             teacher=instance.created_by if hasattr(instance, 'created_by') else None,
#             subject=instance,
#             metric_type='content_created',
#             metric_value=1,
#             metadata={
#                 'subject_name': instance.name,
#                 'grade_level': instance.grade_level,
#                 'description': instance.description
#             }
#         )
        
#         logger.info(f"Subject created: {instance.name}")


# @receiver(post_delete, sender=User)
# def handle_user_deletion(sender, instance, **kwargs):
#     """Handle user deletion"""
#     # Clean up related data
#     logger.info(f"User deleted: {instance.username}")
    
#     # Note: Django's CASCADE will handle most related data deletion
#     # This is just for logging and any additional cleanup needed


# @receiver(post_save, sender=Notification)
# def handle_notification_creation(sender, instance, created, **kwargs):
#     """Handle notification creation"""
#     if created:
#         # Update user's unread count in cache
#         cache_key = f"unread_count_{instance.user.id}"
#         cache.delete(cache_key)
        
#         logger.info(f"Notification created: {instance.user.username} - {instance.title}")


# @receiver(post_save, sender=Notification)
# def handle_notification_read(sender, instance, created, **kwargs):
#     """Handle notification read status change"""
#     if not created and instance.is_read:
#         # Update user's unread count in cache
#         cache_key = f"unread_count_{instance.user.id}"
#         cache.delete(cache_key)
        
#         logger.info(f"Notification read: {instance.user.username} - {instance.title}")


# @receiver(pre_save, sender=StudentProgress)
# def validate_lesson_progress(sender, instance, **kwargs):
#     """Validate lesson progress before saving"""
#     if instance.status == 'COMPLETED' and not instance.completed_at:
#         instance.completed_at = timezone.now()
    
#     if instance.status in ['IN_PROGRESS', 'COMPLETED'] and not instance.started_at:
#         instance.started_at = timezone.now()


# @receiver(pre_save, sender=QuizAttempt)
# def validate_quiz_attempt(sender, instance, **kwargs):
#     """Validate quiz attempt before saving"""
#     if instance.completed_at and not instance.score:
#         # Calculate score if not set
#         total_points = sum(q.points for q in instance.quiz.questions.filter(is_active=True))
#         earned_points = sum(answer.points_earned for answer in instance.answers.all())
        
#         if total_points > 0:
#             instance.score = (earned_points / total_points) * 100
#             instance.is_passed = instance.score >= instance.quiz.passing_score


# @receiver(post_save, sender=LearningStreak)
# def handle_streak_update(sender, instance, created, **kwargs):
#     """Handle learning streak updates"""
#     if not created and instance.current_streak > 0:
#         # Check for streak milestones
#         if instance.current_streak == 7:
#             create_streak_milestone(instance.student, 7)
#         elif instance.current_streak == 30:
#             create_streak_milestone(instance.student, 30)
#         elif instance.current_streak == 100:
#             create_streak_milestone(instance.student, 100)


# def create_streak_milestone(student, streak_days):
#     """Create a streak milestone for a student"""
#     milestone, created = ProgressMilestone.objects.get_or_create(
#         student=student,
#         milestone_type='STREAK_ACHIEVEMENT',
#         title=f"{streak_days}-Day Learning Streak!",
#         defaults={
#             'description': f"Amazing! You've maintained a {streak_days}-day learning streak!",
#             'metadata': {'streak_days': streak_days}
#         }
#     )
    
#     if created:
#         logger.info(f"Streak milestone created: {student.username} - {streak_days} days")


# @receiver(post_save, sender=SubjectProgress)
# def handle_subject_progress_update(sender, instance, created, **kwargs):
#     """Handle subject progress updates"""
#     if not created:
#         # Check if subject is completed (80%+ completion)
#         if instance.total_lessons > 0:
#             completion_rate = (instance.completed_lessons / instance.total_lessons) * 100
            
#             if completion_rate >= 80:
#                 # Create subject completion milestone
#                 milestone, created = ProgressMilestone.objects.get_or_create(
#                     student=instance.student,
#                     milestone_type='SUBJECT_COMPLETION',
#                     title=f"{instance.subject.name} Master!",
#                     defaults={
#                         'description': f"Congratulations! You've completed {instance.subject.name} with {completion_rate:.1f}% completion!",
#                         'metadata': {
#                             'subject_id': instance.subject.id,
#                             'completion_rate': completion_rate
#                         }
#                     }
#                 )
                
#                 if created:
#                     logger.info(f"Subject completion milestone: {instance.student.username} - {instance.subject.name}")


# @receiver(post_save, sender=GradeProgress)
# def handle_grade_progress_update(sender, instance, created, **kwargs):
#     """Handle grade progress updates"""
#     if not created:
#         # Check if grade is completed (80%+ completion)
#         if instance.total_lessons > 0:
#             completion_rate = (instance.completed_lessons / instance.total_lessons) * 100
            
#             if completion_rate >= 80:
#                 # Create grade completion milestone
#                 milestone, created = ProgressMilestone.objects.get_or_create(
#                     student=instance.student,
#                     milestone_type='GRADE_COMPLETION',
#                     title=f"Grade {instance.grade_level} Graduate!",
#                     defaults={
#                         'description': f"Outstanding! You've completed Grade {instance.grade_level} with {completion_rate:.1f}% completion!",
#                         'metadata': {
#                             'grade_level': instance.grade_level,
#                             'completion_rate': completion_rate
#                         }
#                     }
#                 )
                
#                 if created:
#                     logger.info(f"Grade completion milestone: {instance.student.username} - Grade {instance.grade_level}")


# # Additional signal handlers for specific functionality

# @receiver(post_save, sender=QuizResult)
# def handle_quiz_result_creation(sender, instance, created, **kwargs):
#     """Handle quiz result creation"""
#     if created:
#         # Create analytics record for detailed quiz results
#         Analytics.objects.create(
#             student=instance.attempt.student,
#             quiz=instance.attempt.quiz,
#             metric_type='quiz_result_analysis',
#             metric_value=instance.attempt.score or 0,
#             metadata={
#                 'total_time': instance.total_time,
#                 'average_time_per_question': instance.average_time_per_question,
#                 'difficulty_breakdown': instance.difficulty_breakdown,
#                 'improvement_suggestions': instance.improvement_suggestions
#             }
#         )
        
#         logger.info(f"Quiz result created: {instance.attempt.student.username} - {instance.attempt.quiz.title}")


# @receiver(post_save, sender=User)
# def handle_user_role_change(sender, instance, created, **kwargs):
#     """Handle user role changes"""
#     if not created:
#         # Update analytics when user role changes
#         Analytics.objects.create(
#             student=instance if instance.is_student() else None,
#             teacher=instance if instance.is_teacher() else None,
#             parent=instance if instance.is_parent() else None,
#             metric_type='role_change',
#             metric_value=1,
#             metadata={
#                 'old_role': getattr(instance, '_old_role', None),
#                 'new_role': instance.role,
#                 'user_id': instance.id
#             }
#         )
        
#         # Store old role for next save
#         instance._old_role = instance.role


# @receiver(pre_save, sender=User)
# def store_old_role(sender, instance, **kwargs):
#     """Store old role before saving"""
#     if instance.pk:
#         try:
#             old_instance = User.objects.get(pk=instance.pk)
#             instance._old_role = old_instance.role
#         except User.DoesNotExist:
#             instance._old_role = None
#     else:
#         instance._old_role = None

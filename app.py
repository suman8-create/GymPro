from flask import Flask, render_template, request, redirect, url_for, flash, Response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_apscheduler import APScheduler
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from models import db, Member, Attendance, Trainer, Payment, User, NotificationLog
from datetime import date, timedelta, datetime
from collections import Counter
import csv
import io
import os

app = Flask(__name__)

# Look for a DATABASE_URL from Render. If it doesn't exist, use local SQLite.
db_url = os.environ.get('DATABASE_URL', 'sqlite:///gym.db')

# SQLAlchemy requires 'postgresql://' but Render sometimes provides 'postgres://'
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# Set the configurations ONLY ONCE
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-local-secret-key')
app.config['SCHEDULER_API_ENABLED'] = True # Required for APScheduler

db.init_app(app)

# --- Scheduler Setup ---
scheduler = APScheduler()
scheduler.init_app(app)

# The Background Job Logic
def send_automated_reminders():
    # Push app context so the background thread can talk to the database
    with app.app_context():
        today = date.today()
        # Look for anyone expiring in the next 3 days, or already expired
        warning_date = today + timedelta(days=3) 
        
        target_members = Member.query.filter(
            (Member.subscription_end_date <= warning_date) | 
            (Member.subscription_end_date == None)
        ).all()

        emails_sent = 0
        for member in target_members:
            # Check if we already reminded them in the last 7 days
            last_notif = NotificationLog.query.filter_by(member_id=member.id).order_by(NotificationLog.sent_date.desc()).first()
            if last_notif and (datetime.now() - last_notif.sent_date).days < 7:
                continue # Skip to avoid spamming
            
            # Determine message based on state
            if not member.subscription_end_date or member.subscription_end_date < today:
                msg = f"GymPro Alert: Your {member.plan_type} plan has EXPIRED. Please see the front desk to renew."
            else:
                msg = f"GymPro Reminder: Your plan expires soon on {member.subscription_end_date}. Renew early to maintain access!"

            # "Send" the email (Print to console)
            print(f"\n[AUTOMATED SYSTEM] Sending SMS to {member.phone}...")
            print(f"Message: {msg}\n")
            
            # Log it in the database
            db.session.add(NotificationLog(member_id=member.id, message=msg))
            emails_sent += 1
            
        db.session.commit()
        print(f"[AUTOMATED SYSTEM] Job complete. {emails_sent} reminders sent.")

# Schedule the job to run every day at 8:00 AM automatically
scheduler.add_job(id='Daily_Reminders', func=send_automated_reminders, trigger='cron', hour=8, minute=0)
scheduler.start()

# --- Authentication Setup ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# --- Helper Functions ---
def get_plan_days(plan_type):
    if plan_type == 'Monthly': return 30
    if plan_type == 'Quarterly': return 90
    if plan_type == 'Yearly': return 365
    return 30
    
def get_plan_price(plan_type):
    if plan_type == 'Monthly': return 50.0
    if plan_type == 'Quarterly': return 135.0
    if plan_type == 'Yearly': return 500.0
    return 50.0

with app.app_context():
    db.create_all()
    # Seed Data...
    if Trainer.query.count() == 0:
        seed_trainers = [Trainer(name='Arjun Mehta', specialty='Weight Loss'), Trainer(name='Priya Nair', specialty='Strength')]
        db.session.add_all(seed_trainers)
        db.session.commit()
    if User.query.count() == 0:
        db.session.add(User(username='admin', password_hash=generate_password_hash('admin123'), role='admin'))
        for t in Trainer.query.all():
            db.session.add(User(username=t.name.split()[0].lower(), password_hash=generate_password_hash('trainer123'), role='trainer', trainer_id=t.id))
        db.session.commit()

# --- Auth Routes ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('index'))
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and check_password_hash(user.password_hash, request.form.get('password')):
            login_user(user)
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('index'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# --- Main Routes (Kept Identical to Before) ---
@app.route('/')
@login_required
def index():
    search_query = request.args.get('q', '').strip()
    base_query = Member.query
    if current_user.role == 'trainer':
        base_query = base_query.filter_by(trainer_id=current_user.trainer_id)

    members = base_query.filter(Member.name.ilike(f'%{search_query}%')).all() if search_query else base_query.all()
    total_members = base_query.count()
    total_unpaid = base_query.filter((Member.subscription_end_date == None) | (Member.subscription_end_date < date.today())).count()
    today_attendance = Attendance.query.filter_by(date=date.today()).count()

    return render_template('index.html', members=members, total_members=total_members, total_unpaid=total_unpaid, today_attendance=today_attendance, search_query=search_query)

@app.route('/add', methods=['GET', 'POST'])
@admin_required 
def add_member():
    trainers = Trainer.query.all()
    if request.method == 'POST':
        join_date = date.fromisoformat(request.form.get('join_date')) if request.form.get('join_date') else date.today()
        plan_type = request.form.get('plan_type', 'Monthly')
        has_paid = request.form.get('fee_paid') == 'on'
        sub_end_date = join_date + timedelta(days=get_plan_days(plan_type)) if has_paid else None

        new_member = Member(name=request.form.get('name'), phone=request.form.get('phone'), join_date=join_date, subscription_end_date=sub_end_date, plan_type=plan_type, trainer_id=int(request.form.get('trainer_id')) if request.form.get('trainer_id') else None)
        db.session.add(new_member)
        db.session.commit() 
        if has_paid:
            db.session.add(Payment(member_id=new_member.id, amount=get_plan_price(plan_type), payment_date=join_date, plan_credited=plan_type))
            db.session.commit()
        flash('Member added successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('add_member.html', trainers=trainers, today=date.today().isoformat())

@app.route('/mark_attendance/<int:member_id>')
@login_required 
def mark_attendance(member_id):
    member = Member.query.get_or_404(member_id)
    if current_user.role == 'trainer' and member.trainer_id != current_user.trainer_id:
        flash("You can only mark attendance for your own clients.", "danger")
        return redirect(url_for('index'))
    if not Attendance.query.filter_by(member_id=member_id, date=date.today()).first():
        db.session.add(Attendance(member_id=member_id, date=date.today()))
        db.session.commit()
        flash('Attendance marked!', 'success')
    return redirect(url_for('index'))

@app.route('/record_payment/<int:member_id>')
@admin_required
def record_payment(member_id):
    member = Member.query.get_or_404(member_id)
    base_date = member.subscription_end_date if member.subscription_end_date and member.subscription_end_date > date.today() else date.today()
    member.subscription_end_date = base_date + timedelta(days=get_plan_days(member.plan_type))
    db.session.add(Payment(member_id=member.id, amount=get_plan_price(member.plan_type), payment_date=date.today(), plan_credited=member.plan_type))
    db.session.commit()
    flash(f'Payment recorded. Plan extended!', 'success')
    return redirect(url_for('index'))

@app.route('/member/<int:member_id>')
@login_required
def member_detail(member_id):
    member = Member.query.get_or_404(member_id)
    records = Attendance.query.filter_by(member_id=member_id).order_by(Attendance.date.desc()).all()
    payments = Payment.query.filter_by(member_id=member_id).order_by(Payment.payment_date.desc()).all()
    count = len(records)
    badge = ('Champion', 'danger') if count >= 20 else ('Regular', 'success') if count >= 10 else ('Active', 'primary') if count >= 5 else ('Newcomer', 'secondary')
    return render_template('member_detail.html', member=member, records=records, payments=payments, badge=badge, total_days=count)

@app.route('/attendance')
@admin_required
def attendance():
    records = Attendance.query.order_by(Attendance.date.desc()).all()
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_counter = Counter(record.date.weekday() for record in records)
    day_stats = [(day_names[i], day_counter.get(i, 0)) for i in range(7)]
    return render_template('attendance.html', records=records, day_stats=day_stats, peak_day=None, peak_count=0)

@app.route('/export_csv')
@admin_required
def export_csv():
    records = Attendance.query.order_by(Attendance.date.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['Member Name', 'Date', 'Day'])
    for r in records:
        writer.writerow([r.member.name, r.date.strftime('%Y-%m-%d'), r.date.strftime('%A')])
    
    output.seek(0)
    return Response(
        output.getvalue(), 
        mimetype="text/csv", 
        headers={"Content-Disposition": "attachment; filename=attendance.csv"}
    )
@app.route('/trainers')
@admin_required
def trainers(): return render_template('trainers.html', trainers=Trainer.query.all())

@app.route('/add_trainer', methods=['GET', 'POST'])
@admin_required
def add_trainer():
    if request.method == 'POST':
        db.session.add(Trainer(name=request.form.get('name'), specialty=request.form.get('specialty')))
        db.session.commit()
        return redirect(url_for('trainers'))
    return render_template('add_trainer.html')

# --- NEW NOTIFICATION ROUTES ---
@app.route('/admin/notifications')
@admin_required
def notifications():
    logs = NotificationLog.query.order_by(NotificationLog.sent_date.desc()).limit(50).all()
    return render_template('notifications.html', logs=logs)

@app.route('/admin/trigger_reminders', methods=['POST'])
@admin_required
def trigger_reminders():
    # Route for manually testing the automation job
    send_automated_reminders()
    flash('Automated Reminder System triggered successfully!', 'success')
    return redirect(url_for('notifications'))

if __name__ == '__main__':
    app.run(debug=True)
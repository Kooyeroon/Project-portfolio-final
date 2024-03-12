from flask import render_template, url_for, flash, redirect, request, session
from beam import app, db, bcrypt
from beam.forms import RegistrationForm, LoginForm
from beam.models import User, LoadsBeam
from flask_login import login_user, current_user, logout_user, login_required


@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html', title = 'Home')


@app.route("/beam")
@login_required
def beam():
    return render_template('beam.html', title='Beam')

@app.route('/calculate', methods=['POST'])
def calculate():
    l = float(request.form['length'])
    st = request.form['support_type'].strip().lower()  # Ensure st is in lowercase and stripped of any extra whitespace
    lt = request.form['load_type'].strip().lower()  # Ensure st is in lowercase and stripped of any extra whitespace
    lm = float(request.form['load_magnitude'])
    lp = float(request.form['load_position'])

    range_value = 1000
    segment_length = l / range_value
    shear_force = []
    bending_moment = []

    if lt == "distributed_load":

        if st == "pin-pin":
            for i in range(range_value + 1):
                p = i * segment_length

                # Calculate shear force
                shear_force.append(lm * ((l / 2) - p))
                
                # Calculate bending moment
                bending_moment.append(((lm * p) * (l - p)) / 2)

        elif st == "pin-fixed":
            for i in range(range_value + 1):
                p = i * segment_length

                # Calculate shear force
                shear_force.append(lm * (((3 * l) / 8) - p))

                # Calculate bending moment
                bending_moment.append((lm * p) * (((3 * l) / 8) - (p / 2)))

        elif st == "fixed-pin":
            for i in range(range_value + 1):
                p = i * segment_length

                # Calculate shear force
                shear_force.append(lm * (((5 * l) / 8) - p))

                # Calculate bending moment
                bending_moment.append((lm * p) * (((5 * l) / 8) - p/2) - ((lm * l**2) / 8))

        else:  # For any other support type, including "fixed-fixed"
            for i in range(range_value + 1):
                p = i * segment_length

                # Calculate shear force
                shear_force.append(lm * ((l/2) -p))
               
                # Calculate bending moment
                bending_moment.append((lm / 12) * ((6 * l * p) - (l**2) - (6 * p**2)))

    else: 

        if st == "pin-pin":
            for i in range(range_value + 1):
                p = i * segment_length

                # Calculate shear force
                if p <= lp:
                    shear_force.append(lm * (1 - lp / l))
                else:
                    shear_force.append(-lm * (lp / l))

                # Calculate bending moment
                if p <= lp:
                    bending_moment.append(p * lm * (1 - lp / l))
                else:
                    bending_moment.append(lm * lp * (1 - p / l))

        elif st == "pin-fixed":
            for i in range(range_value + 1):
                p = i * segment_length

                # Calculate shear force
                if p <= lp:
                    shear_force.append(((lm * (l - lp) ** 2) * (lp + 2 * l)) / (2 * l ** 3))
                else:
                    shear_force.append(-((lm * lp) * (3 * l ** 2 - lp ** 2)) / (2 * l ** 3))

                # Calculate bending moment
                if p <= lp:
                    bending_moment.append(p * ((lm * (l - lp) ** 2) * (lp + 2 * l)) / (2 * l ** 3))
                else:
                    bending_moment.append((p * ((lm * (l - lp) ** 2) * (lp + 2 * l)) / (2 * l ** 3)) - (lm * (p - lp)))

        elif st == "fixed-pin":
            for i in range(range_value + 1):
                p = i * segment_length

                # Calculate shear force
                if p <= lp:
                    shear_force.append((lm * (l - lp) * (3 * l ** 2 - (l - lp) ** 2)) / (2 * l ** 3))
                else:
                    shear_force.append(-((lm * lp ** 2) * ((l - lp) + 2 * l)) / (2 * l ** 3))

                # Calculate bending moment
                if p <= lp:
                    bending_moment.append(
                        p * ((lm * (l - lp) * (3 * l ** 2 - (l - lp) ** 2)) / (2 * l ** 3)) - ((lm * lp * (l - lp) * (2 * l - lp)) / (2 * l ** 2)))
                else:
                    bending_moment.append(
                        p * ((lm * (l - lp) * (3 * l ** 2 - (l - lp) ** 2)) / (2 * l ** 3)) - ((lm * lp * (l - lp) * (2 * l - lp)) / (2 * l ** 2)) - (lm * (p - (l - lp))))

        else:  # For any other support type, including "fixed-fixed"
            for i in range(range_value + 1):
                p = i * segment_length

                # Calculate shear force
                if p <= lp:
                    shear_force.append((lm * (3 * lp + (l - lp)) * (l - lp) ** 2) / (l ** 3))
                else:
                    shear_force.append(-(lm * (lp + 3 * (l - lp)) * (lp) ** 2) / (l ** 3))

                # Calculate bending moment
                if p <= lp:
                    bending_moment.append((p * (lm * (3 * lp + (l - lp)) * (l - lp) ** 2) / (l ** 3)) - ((lm * lp * (l - lp) ** 2) / (l ** 2)))
                else:
                    bending_moment.append((p * (lm * (3 * lp + (l - lp)) * (l - lp) ** 2) / (l ** 3)) - ((lm * lp * (l - lp) ** 2) / (l ** 2)) - (lm * (p - lp)))

    # Store in SQLite database
    for i in range(range_value + 1):
        position = i * l / range_value
        load = LoadsBeam(position=position, shear_force=shear_force[i], bending_moment=bending_moment[i], user=current_user)
        db.session.add(load)

    db.session.commit()

    flash('Congratulations! Your calculation was successful and sent to the SQLite database.', 'success')

    return redirect(url_for('beam'))


@app.route('/diagram', methods=['GET', 'POST'])
def diagram():
    if request.method == 'GET':
        # Fetch data from SQLite for the current user
        data_query = LoadsBeam.query.filter_by(user_id=current_user.id)
        
        # Apply with_entities() to the query object before executing it
        data_query = data_query.with_entities(LoadsBeam.position, LoadsBeam.shear_force, LoadsBeam.bending_moment)
        
        # Execute the query to get the result
        data = data_query.all()
        # Convert the list of Row objects to a list of dictionaries
        data_dict_list = []
        for row in data:
            data_dict_list.append(row._asdict())  # Convert Row object to dictionary
        
        return render_template('diagram.html', beam_data=data_dict_list)
    else:
        # Handle POST request if needed
        pass

@app.route('/clear_data', methods=['POST', 'GET'])
def clear_data():
    if request.method == 'POST':
        # Fetch data from SQLite for the current user
        loads_to_delete = LoadsBeam.query.filter_by(user_id=current_user.id).all()

        # Delete the LoadsBeam objects associated with the current user
        for load in loads_to_delete:
            db.session.delete(load)
        
        # Commit changes to the database
        db.session.commit()

        # Clear the user session
        session.pop('user_id', None)

        # Flash a success message
        flash("Data cleared successfully!", "success")
        
        # Redirect to the 'beam' route or adjust the redirection as needed
        return redirect(url_for('beam'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user_to_create = User(username=form.username.data,
                              email_address=form.email.data,
                              password=form.password.data)
        db.session.add(user_to_create)
        db.session.commit()
        login_user(user_to_create)
        flash(f"Account created successfully! You are now logged in as {user_to_create.username}", category='success')
        return redirect(url_for('beam'))
    if form.errors != {}: #If there are not errors from the validations
        for err_msg in form.errors.values():
            flash(f'There was an error with creating a user: {err_msg}', category='danger')

    return render_template('register.html', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('beam'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('beam'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    flash("You have been logged out!", category='info')
    return redirect(url_for('register'))

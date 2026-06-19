from flask import Blueprint, request, jsonify, render_template

chatbot_bp = Blueprint("chatbot", __name__)

@chatbot_bp.route("/chatbot_page")
def chatbot_page():
    return render_template("chatbot.html")


@chatbot_bp.route("/chatbot", methods=["POST"])
def chatbot():

    data = request.get_json()
    message = data.get("message", "").lower()

    category = "Other"
    title = "General Campus Complaint"
    description = message
    priority = "Normal"

    # INTERNET
    if any(word in message for word in ["wifi","internet","network","connection"]):
        category = "Internet"
        title = "Internet Connectivity Issue"

    # CLASSROOM
    elif any(word in message for word in ["classroom","chair","chairs","bench","board","projector"]):
        category = "Classroom"
        title = "Classroom Facility Issue"

    # LIBRARY
    elif any(word in message for word in ["library","book","reading","study"]):
        category = "Library"
        title = "Library Facility Issue"

    # CAFETERIA
    elif any(word in message for word in ["cafeteria","canteen","food","meal"]):
        category = "Cafeteria"
        title = "Cafeteria Service Issue"

    # HOSTEL
    elif any(word in message for word in ["hostel","room","bathroom","water","fan"]):
        category = "Hostel"
        title = "Hostel Facility Issue"

    return jsonify({
        "title": title,
        "category": category,
        "priority": priority,
        "description": description
    })
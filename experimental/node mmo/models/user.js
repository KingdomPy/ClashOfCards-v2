const mongoose = require('mongoose');

//Users Schema
let userSchema = mongoose.Schema({
	username:{
		type: String,
		required: true,
	},
	email:{
		type: String,
		required: true,
	},
	password:{
		type: String,
		required: true,
	},
});

const User = mongoose.model('User', userSchema);

module.exports = User;
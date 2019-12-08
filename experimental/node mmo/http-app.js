const express = require('express');
const http = require('http');
const path = require('path');
const mongoose = require('mongoose');
const bcrypt = require('bcrypt');
const session = require('express-session');
const config = require('./config/database');

const PORT = process.env.PORT || 80;
const database = config.MongoURI;

mongoose.connect(database, { useNewUrlParser: true, useUnifiedTopology: true})
  .then(() => console.log('MongoDB Connected...'))
  .catch(err => console.log(err));

var app = express();
var httpServer = http.Server(app);

app.use(express.urlencoded({ extended: false })) // for parsing application/x-www-form-urlencoded

app.get('/', function(request, response) {
	response.sendFile(__dirname + '/assets/index.html');
});

app.post('/login', function(request, response) {
	const {username, password, email} = request.body;
	let errors = [];
	if (!username || !password) {
		errors.push('Fill in all fields');
	}
	if ((username.length < 3 || username.length > 26) && !username.includes(" ")) {
		errors.push('Username must be between 3 and 26 characters');
	}
	if ((password.length < 6 || password.length > 26) && !password.includes(" ")) {
		errors.push('Password must be between 6 and 26 characters');
	}
	let status;
	if (errors.length > 0) {
		status = 0;
	} else{
		status = 1;
	}
	response.send({status:status, errors:errors});
});

app.post('/signup', function(request, response) {
	const {username, password, email} = request.body;
	let errors = [];
	if (!username || !email || !password) {
		errors.push('Fill in all fields');
	}
	if ((username.length < 3 || username.length > 26) && !username.includes(" ")) {
		errors.push('Username must be between 3 and 26 characters');
	}
	if ((password.length < 6 || password.length > 26) && !password.includes(" ")) {
		errors.push('Password must be between 6 and 26 characters');
	}
	if ((email == "" || email == null) && !email.includes("@") && email.length < 52) {
		errors.push('Email can not exceed 52 characters');
	}
	let status;
	if (errors.length > 0) {
		status = 0;
	} else{
		status = 1;
	}
	response.send({status:status, errors:errors});
});

app.use('/assets', express.static(__dirname + '/assets'));

httpServer.listen(PORT);
console.log("Https server has started.");

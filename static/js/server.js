// const express = require('express');
// const multer = require('multer');
// const mysql = require('mysql');
// const cors = require('cors');
// const path = require('path');

// const app = express();
// app.use(cors());
// app.use(express.static('uploads'));

// const db = mysql.createConnection({
//     host: 'localhost',
//     user: 'root',
//     password: '',
//     database: 'file_upload_db'
// });

// db.connect(err => {
//     if (err) throw err;
//     console.log('MySQL Connected...');
// });

// const storage = multer.diskStorage({
//     destination: './uploads/',
//     filename: (req, file, cb) => {
//         cb(null, Date.now() + path.extname(file.originalname));
//     }
// });

// const upload = multer({ storage });

// app.post('/upload', upload.single('file'), (req, res) => {
//     const { name, email } = req.body;
//     const filePath = req.file.filename;

//     const sql = 'INSERT INTO uploads (name, email, file_path) VALUES (?, ?, ?)';
//     db.query(sql, [name, email, filePath], (err, result) => {
//         if (err) {
//             console.error(err);
//             res.status(500).send('Database Error');
//         } else {
//             res.send('Successfully Uploaded');
//         }
//     });
// });

// app.listen(3000, () => {
//     console.log('Server running on port 3000');
// });

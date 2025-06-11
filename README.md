# Resume Analysis Tool - Advanced Scoring System

A powerful AI-powered resume analysis tool that evaluates candidates against job requirements using a sophisticated 2-criteria scoring system. Built with Gradio and Claude AI.

## 🌟 Features

- **Smart Resume Analysis**: Upload multiple resumes (PDF, DOCX, TXT) for batch processing
- **Advanced Scoring System**: 
  - Job Description Similarity (65% weight)
  - Designation Match (35% weight)
- **Interactive Results**: 
  - Color-coded match indicators (🟢 Good | 🟠 Considerable | 🔴 Reject)
  - Resizable columns for optimal viewing
  - Delete candidates with one click
  - Fullscreen view for detailed analysis
- **Export Capabilities**: Download results as CSV
- **Real-time Validation**: Character count for job descriptions
- **Responsive Design**: Works on desktop and mobile

## 🚀 Scoring Methodology

### Job Description Similarity (65% weight - Max 6.5 points)
- **High Overlap (5.5-6.5 points)**: 70%+ responsibility match, same industry/domain
- **Moderate Overlap (3.5-5.4 points)**: 40-69% responsibility match, related industry
- **Low Overlap (0-3.4 points)**: <40% responsibility match, different industry

### Designation Match (35% weight - Max 3.5 points)
- **Exact/Similar Match (2.5-3.5 points)**: Same title or very similar level
- **Related Match (1.5-2.4 points)**: Adjacent level or related function
- **Poor Match (0-1.4 points)**: Unrelated title or major level gap

### Final Decision Logic
- **Score 8-10**: GOOD MATCH
- **Score 5-7**: CONSIDERABLE MATCH
- **Score 1-4**: REJECT

## 🛠️ Installation & Setup

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/resume-analysis-tool.git
   cd resume-analysis-tool
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variable**
   ```bash
   export CLAUDE_API_KEY="your-claude-api-key-here"
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

### Docker Deployment

1. **Build the image**
   ```bash
   docker build -t resume-analysis-tool .
   ```

2. **Run the container**
   ```bash
   docker run -p 7860:7860 -e CLAUDE_API_KEY="your-api-key" resume-analysis-tool
   ```

## 🌐 Deploy to Render

### Option 1: Connect GitHub Repository

1. **Fork this repository** to your GitHub account

2. **Create a new Web Service** on [Render](https://render.com)
   - Connect your GitHub repository
   - Select this repository

3. **Configure the service**:
   - **Name**: `resume-analysis-tool`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`

4. **Set Environment Variables**:
   - `CLAUDE_API_KEY`: Your Claude API key
   - `PORT`: `7860` (optional, defaults to 7860)

5. **Deploy**: Click "Create Web Service"

### Option 2: Manual Deployment

1. **Create new Web Service** on Render

2. **Upload your code** or connect via Git

3. **Configure**:
   ```
   Runtime: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: python app.py
   ```

4. **Environment Variables**:
   ```
   CLAUDE_API_KEY=your_claude_api_key_here
   ```

## 📝 Usage Instructions

1. **Upload Resumes**: Add multiple resume files (PDF, DOCX, TXT format)

2. **Define Job Requirements**:
   - Enter the job title
   - Describe roles and responsibilities (max 1000 characters)

3. **Analyze**: Click "Analyze Multiple Resumes"

4. **Review Results**:
   - View color-coded match status
   - Read detailed scoring and reasoning
   - Use fullscreen mode for better visibility
   - Delete unwanted candidates

5. **Export**: Download results as CSV for further analysis

## 🔧 Configuration

### Environment Variables

- `CLAUDE_API_KEY` (Required): Your Anthropic Claude API key
- `PORT` (Optional): Port number for the application (default: 7860)

### File Limits

- Maximum 10 resume files per batch
- Supported formats: PDF, DOCX, TXT
- Job description limit: 1000 characters

## 🔒 Security

- API keys are handled through environment variables
- No data is stored permanently on the server
- Files are processed in memory and discarded after analysis

## 🛟 Troubleshooting

### Common Issues

1. **API Key Not Configured**
   - Ensure `CLAUDE_API_KEY` environment variable is set
   - Verify your Claude API key is valid

2. **File Upload Errors**
   - Check file format (PDF, DOCX, TXT only)
   - Ensure file size is reasonable
   - Try uploading files one by one

3. **Analysis Fails**
   - Check internet connection
   - Verify API key permissions
   - Review job description length (max 1000 chars)

### Performance Tips

- Upload smaller batches (5-7 resumes) for faster processing
- Use concise but comprehensive job descriptions
- Clear old results before analyzing new batches

## 📊 Output Format

The tool provides detailed analysis including:

- **Candidate Information**: Name, email, phone, current company/role
- **Experience**: Total years of experience
- **Scoring Breakdown**: Job description score, designation score, final score
- **Recommendation**: Good Match, Considerable Match, or Reject
- **Reasoning**: Detailed explanation of the scoring decision

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Gradio](https://gradio.app/) for the web interface
- Powered by [Anthropic's Claude](https://www.anthropic.com/) for AI analysis
- Uses [PyPDF2](https://pypdf2.readthedocs.io/) for PDF processing
- Document processing with [python-docx](https://python-docx.readthedocs.io/)

## 📞 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review existing GitHub issues
3. Create a new issue with detailed information

---

**Made with ❤️ for efficient recruitment processes**

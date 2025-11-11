"""
Claude API Integration Module
Handles real-time legal analysis of meeting transcripts using Claude
"""

import time
from typing import Optional, List, Dict, Callable
from datetime import datetime
from anthropic import Anthropic
import threading


class ClaudeAnalyzer:
    """Analyzes meeting transcripts using Claude AI for legal insights"""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        """
        Initialize Claude analyzer

        Args:
            api_key: Anthropic API key
            model: Claude model to use
        """
        self.api_key = api_key
        self.model = model
        self.client = Anthropic(api_key=api_key)

        self.analysis_history: List[Dict] = []
        self.is_analyzing = False
        self.callbacks = []

        # System prompt for legal analysis
        self.system_prompt = """You are a legal assistant analyzing meeting transcripts in real-time.
Your role is to:
1. Identify key legal points, issues, and action items
2. Highlight important deadlines, dates, and commitments
3. Flag potential legal concerns or risks
4. Summarize decisions and agreements
5. Note any follow-up tasks or required documentation

Provide concise, actionable insights focused on legal practice management.
Format your response in clear sections with bullet points."""

    def analyze_transcript(self, transcript_text: str,
                          context: Optional[str] = None,
                          custom_prompt: Optional[str] = None) -> Optional[str]:
        """
        Analyze transcript text using Claude

        Args:
            transcript_text: The transcript to analyze
            context: Additional context about the meeting
            custom_prompt: Custom analysis prompt (overrides default)

        Returns:
            Analysis text from Claude
        """
        if not transcript_text or not transcript_text.strip():
            return None

        try:
            # Build the user message
            user_message = self._build_analysis_prompt(
                transcript_text,
                context,
                custom_prompt
            )

            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=self.system_prompt,
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )

            analysis = response.content[0].text

            # Store in history
            self.analysis_history.append({
                'timestamp': datetime.now(),
                'transcript': transcript_text,
                'context': context,
                'analysis': analysis
            })

            return analysis

        except Exception as e:
            print(f"Error analyzing transcript: {e}")
            return None

    def analyze_incremental(self, new_segment: str,
                           previous_analysis: Optional[str] = None) -> Optional[str]:
        """
        Analyze new transcript segment with context from previous analysis

        Args:
            new_segment: New transcript segment to analyze
            previous_analysis: Previous analysis for context

        Returns:
            Updated analysis from Claude
        """
        try:
            prompt = f"""New transcript segment:
{new_segment}

"""
            if previous_analysis:
                prompt += f"""Previous analysis:
{previous_analysis}

Please update your analysis with insights from the new segment,
highlighting any new information or changes."""
            else:
                prompt += "Please provide an initial analysis of this segment."

            return self.analyze_transcript(new_segment, custom_prompt=prompt)

        except Exception as e:
            print(f"Error in incremental analysis: {e}")
            return None

    def get_meeting_summary(self, full_transcript: str,
                           meeting_title: Optional[str] = None) -> Optional[str]:
        """
        Generate comprehensive meeting summary

        Args:
            full_transcript: Complete meeting transcript
            meeting_title: Optional meeting title

        Returns:
            Detailed summary from Claude
        """
        try:
            prompt = f"""Please provide a comprehensive summary of this meeting transcript.

"""
            if meeting_title:
                prompt += f"Meeting: {meeting_title}\n\n"

            prompt += f"""Transcript:
{full_transcript}

Include:
1. Meeting Overview
2. Key Discussion Points
3. Decisions Made
4. Action Items (who, what, when)
5. Important Deadlines
6. Legal Concerns or Risks
7. Follow-up Required
8. Next Steps

Be specific and actionable."""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=8192,
                system=self.system_prompt,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            return response.content[0].text

        except Exception as e:
            print(f"Error generating meeting summary: {e}")
            return None

    def extract_action_items(self, transcript: str) -> Optional[List[Dict]]:
        """
        Extract structured action items from transcript

        Args:
            transcript: Meeting transcript

        Returns:
            List of action items with assignee, task, and deadline
        """
        try:
            prompt = f"""Analyze this transcript and extract all action items.

{transcript}

For each action item, provide:
- Who: Person responsible
- What: Task description
- When: Deadline or timeframe
- Priority: High/Medium/Low

Return as a structured list."""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system="You are a legal assistant extracting action items from meetings.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Parse response into structured format
            action_items_text = response.content[0].text

            # Store in history
            self.analysis_history.append({
                'timestamp': datetime.now(),
                'type': 'action_items',
                'analysis': action_items_text
            })

            return action_items_text

        except Exception as e:
            print(f"Error extracting action items: {e}")
            return None

    def identify_legal_issues(self, transcript: str) -> Optional[str]:
        """
        Identify potential legal issues in the transcript

        Args:
            transcript: Meeting transcript

        Returns:
            Analysis of legal issues and concerns
        """
        try:
            prompt = f"""Review this transcript and identify any legal issues, risks, or concerns.

{transcript}

Focus on:
- Statute of limitations mentions
- Disclosure obligations
- Conflicts of interest
- Ethical considerations
- Regulatory compliance
- Contract terms or disputes
- Evidence preservation needs

Provide specific recommendations for each issue identified."""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=self.system_prompt,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            return response.content[0].text

        except Exception as e:
            print(f"Error identifying legal issues: {e}")
            return None

    def suggest_follow_up(self, transcript: str) -> Optional[str]:
        """
        Suggest follow-up questions or actions

        Args:
            transcript: Meeting transcript

        Returns:
            Suggested follow-up items
        """
        try:
            prompt = f"""Based on this meeting transcript, suggest follow-up questions,
research topics, or actions that should be taken.

{transcript}

Consider:
- Information gaps that need clarification
- Legal research needed
- Documents to request or review
- Witnesses to interview
- Experts to consult
- Deadlines to calendar"""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=self.system_prompt,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            return response.content[0].text

        except Exception as e:
            print(f"Error suggesting follow-up: {e}")
            return None

    def _build_analysis_prompt(self, transcript: str,
                              context: Optional[str] = None,
                              custom_prompt: Optional[str] = None) -> str:
        """Build the analysis prompt"""
        if custom_prompt:
            return custom_prompt

        prompt = "Analyze this meeting transcript:\n\n"

        if context:
            prompt += f"Context: {context}\n\n"

        prompt += f"Transcript:\n{transcript}\n\n"
        prompt += "Provide key insights, action items, and legal considerations."

        return prompt

    def get_analysis_history(self) -> List[Dict]:
        """Get all analysis history"""
        return self.analysis_history.copy()

    def clear_history(self):
        """Clear analysis history"""
        self.analysis_history = []

    def export_analysis(self, filepath: str, analysis_text: str,
                       meeting_title: Optional[str] = None):
        """
        Export analysis to file

        Args:
            filepath: Path to save analysis
            analysis_text: Analysis content
            meeting_title: Optional meeting title
        """
        from pathlib import Path

        output = []

        if meeting_title:
            output.append(f"Meeting Analysis: {meeting_title}")
            output.append("=" * 80)
            output.append("")

        output.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output.append("")
        output.append(analysis_text)

        Path(filepath).write_text("\n".join(output), encoding='utf-8')


class RealTimeAnalyzer:
    """Performs real-time analysis as transcript is generated"""

    def __init__(self, claude_analyzer: ClaudeAnalyzer,
                 analysis_interval: int = 60):
        """
        Initialize real-time analyzer

        Args:
            claude_analyzer: ClaudeAnalyzer instance
            analysis_interval: Seconds between analyses
        """
        self.analyzer = claude_analyzer
        self.analysis_interval = analysis_interval

        self.is_running = False
        self.analysis_thread = None
        self.current_transcript = ""
        self.last_analysis = None
        self.last_analysis_time = None

        self.callbacks = []

    def start(self, on_analysis: Optional[Callable] = None):
        """
        Start real-time analysis

        Args:
            on_analysis: Callback when new analysis is available
        """
        if self.is_running:
            return

        self.is_running = True
        self.last_analysis_time = time.time()

        if on_analysis:
            self.callbacks.append(on_analysis)

        self.analysis_thread = threading.Thread(target=self._analysis_loop)
        self.analysis_thread.daemon = True
        self.analysis_thread.start()

    def stop(self):
        """Stop real-time analysis"""
        self.is_running = False

        if self.analysis_thread:
            self.analysis_thread.join(timeout=5)

    def update_transcript(self, transcript: str):
        """
        Update current transcript for analysis

        Args:
            transcript: Current full transcript
        """
        self.current_transcript = transcript

    def _analysis_loop(self):
        """Main analysis loop"""
        while self.is_running:
            try:
                current_time = time.time()

                # Check if it's time to analyze
                if current_time - self.last_analysis_time >= self.analysis_interval:
                    if self.current_transcript.strip():
                        # Perform analysis
                        analysis = self.analyzer.analyze_incremental(
                            self.current_transcript,
                            self.last_analysis
                        )

                        if analysis:
                            self.last_analysis = analysis
                            self.last_analysis_time = current_time

                            # Call callbacks
                            for callback in self.callbacks:
                                try:
                                    callback(analysis)
                                except Exception as e:
                                    print(f"Error in analysis callback: {e}")

                time.sleep(5)  # Check every 5 seconds

            except Exception as e:
                print(f"Error in analysis loop: {e}")
                time.sleep(5)

    def get_last_analysis(self) -> Optional[str]:
        """Get the most recent analysis"""
        return self.last_analysis

import io
import re
import xlsxwriter
import json
from django.conf import settings
from django.http import HttpResponse

from xlsxwriter.utility import xl_rowcol_to_cell
from democracy.models import SectionComment

from .section_comment import SectionCommentSerializer


class HearingReport(object):

    def __init__(self, json, context=None):
        self.json = json
        self.buffer = io.BytesIO()
        self.xlsdoc = xlsxwriter.Workbook(self.buffer, {'in_memory': True})
        self.hearing_worksheet = self.xlsdoc.add_worksheet('Hearing')
        self.hearing_worksheet.set_landscape()
        self.hearing_worksheet_active_row = 0
        self.section_worksheet_active_row = 0

        self.format_bold = self.xlsdoc.add_format({'bold': True})
        self.format_merge_title = self.xlsdoc.add_format({'align': 'center', 'underline': True})
        self.format_percent = self.xlsdoc.add_format({'num_format': '0 %'})

        self.context = context

    def add_hearing_row(self, label, content):
        row = self.hearing_worksheet_active_row
        self.hearing_worksheet.write(row, 0, label, self.format_bold)
        self.hearing_worksheet.write(row, 1, self.mitigate_cell_formula_injection(content))
        self.hearing_worksheet_active_row += 1

    def _get_default_translation(self, field):
        lang = settings.LANGUAGE_CODE
        if field.get(lang):
            return field.get(lang)
        for lang, value in field.items():
            if value:
                return value

    def generate_hearing_worksheet(self):
        self.hearing_worksheet.set_column('A:A', 20)
        self.hearing_worksheet.set_column('B:B', 200)

        # add header to hearing worksheet
        self.hearing_worksheet.set_header(self._get_default_translation(self.json['title']))

        for lang, title in self.json['title'].items():
            self.add_hearing_row('Title (%s)' % lang, title)
        self.add_hearing_row('Created', self.json['created_at'])
        self.add_hearing_row('Close', self.json['close_at'])
        # self.add_hearing_row('Author', self.json['created_by'])
        for lang, abstract in self.json['abstract'].items():
            self.add_hearing_row('Abstract (%s)' % lang, abstract)
        for lang, borough in self.json['borough'].items():
            self.add_hearing_row('Borough (%s)' % lang, borough)
        self.add_hearing_row('Labels', str('%s' % ', '.join([self._get_default_translation(label['label']) for label in
                                                            self.json['labels']])))
        self.add_hearing_row('Comments', str(self.json['n_comments']))
        self.add_hearing_row('Sections', str(len(self.json['sections'])))

    def add_section_worksheet(self, section, section_index):
        section_name = ""
        # main section name is always type name
        if section['type'] == 'main':
            section_name = section['type_name_singular']
        else:
            # sub section names use their title or type name if title doesnt exist
            title = self._get_default_translation(section['title'])
            if title:
                section_name = self._get_default_translation(section['title'])
            else:
                section_name = section['type_name_singular']

        # worksheet name must be <= 31 chars and doc cannot have duplicate sheet names
        # duplicates are named like "sheetname(n)"
        if self.xlsdoc.get_worksheet_by_name(section_name) != None:
            section_name = f"{section_name[:28]}({section_index})"

        # remove special characters from worksheet names to avoid potential naming issues
        section_worksheet = self.xlsdoc.add_worksheet(re.sub(r"\W+|_", " ", section_name[:31]))
        section_worksheet.set_landscape()
        section_worksheet.set_column('A:A', 50)
        section_worksheet.set_column('B:B', 15)
        section_worksheet.set_column('C:C', 10)
        section_worksheet.set_column('D:D', 5)
        section_worksheet.set_column('E:E', 50)
        section_worksheet.set_column('F:F', 200)
        section_worksheet.set_column('G:G', 100)
        section_worksheet.set_column('H:H', 100)

        # add section title
        self.section_worksheet_active_row = 0
        section_worksheet.write(self.section_worksheet_active_row, 0, 'Section', self.format_bold)
        self.section_worksheet_active_row += 1
        section_worksheet.write(self.section_worksheet_active_row, 0, self.mitigate_cell_formula_injection(section_name))
        self.section_worksheet_active_row += 2

        # add comments
        self.add_section_comments(section, section_worksheet)

        # add some space between comments and polls
        self.section_worksheet_active_row += 4

        # add polls
        self.add_section_polls(section, section_worksheet)

    
    def add_section_comments(self, section, section_worksheet):
        '''
        Content        | Created | Votes | Label   | Map comment        | Geojson      | Images
        "comment text" | "date"  | num   | "label" | "map comment text" | "geo data"   | "url"
        "comment text" | "date"  | num   | "label" | "map comment text" | "geo data"   | "url"
        '''

        # add comments title
        row = self.section_worksheet_active_row
        section_worksheet.merge_range(row, 0, row, 4, 'Comments', self.format_merge_title)
        self.section_worksheet_active_row += 1

        # add column headers
        row = self.section_worksheet_active_row
        # author names shouldnt be included in outgoing files unless masked somehow
        #section_worksheet.write(row, 0, 'Author', self.format_bold)
        section_worksheet.write(row, 0, 'Content', self.format_bold)
        section_worksheet.write(row, 1, 'Created', self.format_bold)
        section_worksheet.write(row, 2, 'Votes', self.format_bold)
        section_worksheet.write(row, 3, 'Label', self.format_bold)
        section_worksheet.write(row, 4, 'Map comment', self.format_bold)
        section_worksheet.write(row, 5, 'Geojson', self.format_bold)
        section_worksheet.write(row, 6, 'Images', self.format_bold)

        self.section_worksheet_active_row += 1

        # loop through comments in current section
        comments = [SectionCommentSerializer(c, context=self.context).data
                    for c in SectionComment.objects.filter(section=section['id'])]
        for comment in comments:
            self.add_comment_row(comment, section_worksheet)

    def add_comment_row(self, comment, section_worksheet):
        '''
        "comment text" | "date"  | num   | "label" | "map comment text" | "geo data"   | "url"
        '''
        row = self.section_worksheet_active_row
        # author names shouldnt be included in outgoing files unless masked somehow
        # section_worksheet.write(row, 0, comment['author_name'])
        # add content
        section_worksheet.write(row, 0, self.mitigate_cell_formula_injection(comment['content']))
        # add creation date
        section_worksheet.write(row, 1, comment['created_at'])
        # add votes
        section_worksheet.write(row, 2, comment['n_votes'])
        # add label
        section_worksheet.write(row, 3, self.mitigate_cell_formula_injection(
            self._get_default_translation(comment['label'].get('label')
                if comment['label'] else {})))
        # add map comment
        section_worksheet.write(row, 4, self.mitigate_cell_formula_injection(comment['map_comment_text']))
        # add geojson
        section_worksheet.write(row, 5, self.mitigate_cell_formula_injection(json.dumps(comment['geojson'])))
         # add img
        section_worksheet.write(row, 6, ','.join(
            image['url'] for image in comment['images']))
        self.section_worksheet_active_row += 1

    def add_section_polls(self, section, section_worksheet):
        '''
        Poll question | Poll type | Total votes | How many people answered the question
        "question?"   | "type"    | num         | num
        Options       | Votes     | Votes % 
        "1) option"   | 1         | 10%    
        "2) option"   | 9         | 90%    
        -- empty rows after each question --
        '''
        questions = section['questions']

        # add polls title if polls exist
        if len(questions) > 0:
            row = self.section_worksheet_active_row
            section_worksheet.merge_range(row, 0, row, 4, 'Polls', self.format_merge_title)
            self.section_worksheet_active_row += 1

        # add question data for each question
        for question in questions:
            self.add_poll_question_rows(question, section_worksheet)
            # add space between questions
            self.section_worksheet_active_row += 2


    def add_poll_question_rows(self, question, section_worksheet):
        '''
        Poll question | Poll type | Total votes | how many people answered the question
        "question?"   | "type"    | num         | num
        '''
        row = self.section_worksheet_active_row
        chart_location = (row, 5) # set chart to start on the same row as headers
        # headers
        section_worksheet.write(row, 0, 'Poll question', self.format_bold)
        section_worksheet.write(row, 1, 'Poll type', self.format_bold)
        section_worksheet.write(row, 2, 'Total votes', self.format_bold)
        section_worksheet.write(row, 3, 'How many people answered the question', self.format_bold)
        self.section_worksheet_active_row += 1

        # options total vote count
        options = question['options']
        total_options_answers = 0
        for option in options:
            total_options_answers += option['n_answers']

        # values under headers
        row = self.section_worksheet_active_row
        question_text = self._get_default_translation(question['text'])

        section_worksheet.write(row, 0, self.mitigate_cell_formula_injection(question_text))
        section_worksheet.write(row, 1, question['type'])
        section_worksheet.write(row, 2, total_options_answers)
        section_worksheet.write(row, 3, question['n_answers'])
        # store n_answers cell location for option answer % calculation
        total_answers_cell = xl_rowcol_to_cell(row, 2)
        self.section_worksheet_active_row += 1

        # add option rows, store option cell info
        option_cells = self.add_poll_question_option_rows(options, total_answers_cell,
            section_worksheet)

        # add space after options to make room for chart (2 rows per option)
        empty_rows_after_options = len(options) * 2
        self.section_worksheet_active_row += empty_rows_after_options
        # add chart
        self.add_poll_question_chart(question_text, option_cells, chart_location,
            section_worksheet, empty_rows_after_options)

    
    def add_poll_question_option_rows(self, options, total_answers_cell, section_worksheet):
        '''
        Options     | Votes | Votes % 
        "1) option" | 1     | 10 %    
        '''
        row = self.section_worksheet_active_row
        # headers
        section_worksheet.write(row, 0, 'Options', self.format_bold)
        section_worksheet.write(row, 1, 'Votes', self.format_bold)
        section_worksheet.write(row, 2, 'Votes %', self.format_bold)
        self.section_worksheet_active_row += 1

        # store category and value start locations for later calculations
        categories_start = (self.section_worksheet_active_row, 0)
        values_start = (self.section_worksheet_active_row, 2)
        # values under headers
        for index, option in enumerate(options, start=1):
            row = self.section_worksheet_active_row
            section_worksheet.write(row, 0, f"{index}) {self._get_default_translation(option['text'])}")
            section_worksheet.write(row, 1, option['n_answers'])
            section_worksheet.write(row, 2, f"={xl_rowcol_to_cell(row, 1)}/{total_answers_cell}", self.format_percent)
            self.section_worksheet_active_row += 1

        # store category and value end locations for later calculations
        categories_end = (self.section_worksheet_active_row-1, 0) # -1 row to not include empty row
        values_end = (self.section_worksheet_active_row-1, 2) # -1 row to not include empty row

        # return dict containing option cell info
        return {
            'categories_start': categories_start,
            'values_start': values_start,
            'categories_end': categories_end,
            'values_end': values_end,
            'option_count': len(options)
            }
    
    def add_poll_question_chart(self, question_text, option_cells, chart_location,
        section_worksheet, empty_rows_after_options = 0, ):        
        chart = self.xlsdoc.add_chart({'type': 'bar'})
        # Configure the series.
        # [sheetname, first_row, first_col, last_row, last_col]
        section_name = section_worksheet.get_name()
        chart.add_series({
            'categories': [section_name, option_cells['categories_start'][0], option_cells['categories_start'][1],
                option_cells['categories_end'][0], option_cells['categories_end'][1]], 
            'values':     [section_name, option_cells['values_start'][0], option_cells['values_start'][1],
                option_cells['values_end'][0], option_cells['values_end'][1]],
        })

        # Add a chart title and remove series title
        chart.set_title ({
            'name': question_text,
            'name_font': {'name': 'Calibri', 'size': 14, 'bold': False}
        }) # poll question
        chart.set_legend({'none': True}) # removes "series 1" chart title
        
        # chart and axis styles
        chart.set_x_axis({
            'max': 1, # percent scale to always be up to 100%
            'num_font': {'name': 'Calibri', 'size': 9},
        })
        chart.set_y_axis({
            'num_font': {'name': 'Calibri', 'size': 9},
        })

        # calculate chart height
        # standard row pixel height is 20px
        # height = (header rows (3) + option rows + empty rows) * row height
        option_count = option_cells['option_count']
        chart_height = (3 + option_count + empty_rows_after_options) * 20
        chart.set_size({'width': 480, 'height': chart_height})

        # Insert the chart into the worksheet.
        section_worksheet.insert_chart(chart_location[0], chart_location[1], chart)


    def get_xlsx(self):
        self.generate_hearing_worksheet()

        sections = self.json['sections']
        for section_index, section in enumerate(sections, start=0):
            self.add_section_worksheet(section, section_index)

        self.xlsdoc.close()

        return self.buffer.getvalue()

    def get_response(self):
        response = HttpResponse(
            self.get_xlsx(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        # remove special characters from filename to avoid potential file naming issues
        response['Content-Disposition'] = 'attachment; filename={filename}.xlsx'.format(
            filename=re.sub(r"\W+|_", " ", self._get_default_translation(self.json['title'])))
        return response

    # Mitigate formula injection
    # Prefix cell content starting with =, +, -, " or @ with single quote (').
    # The prefix will make the content be read as text instead of formula.
    def mitigate_cell_formula_injection(self, cell_content):
        unallowed_characters = ['=', '+', '-', '"', '@']
        if cell_content and len(cell_content) > 0:
            if cell_content[0] in unallowed_characters:
                return f"'{cell_content}"

        return cell_content

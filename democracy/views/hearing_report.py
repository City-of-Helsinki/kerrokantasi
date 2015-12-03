import io

import xlsxwriter
from django.http import HttpResponse

from democracy.models import SectionComment

from .section_comment import SectionCommentSerializer


def format_user_dict(user_dict):
    if not user_dict:  # pragma: no cover
        return None
    return user_dict["username"]


class HearingReport(object):

    def __init__(self, json):
        self.json = json
        self.buffer = io.BytesIO()
        self.xlsdoc = xlsxwriter.Workbook(self.buffer, {'in_memory': True})
        self.hearing_worksheet = self.xlsdoc.add_worksheet('Hearing')
        self.hearing_worksheet.set_landscape()
        self.hearing_worksheet_active_row = 0
        self.comments_worksheet = self.xlsdoc.add_worksheet('Comments')
        self.comments_worksheet.set_landscape()
        self.comments_worksheet_active_row = 0
        self.format_bold = self.xlsdoc.add_format({'bold': True})

    def add_hearing_row(self, label, content):
        row = self.hearing_worksheet_active_row
        self.hearing_worksheet.write(row, 0, label, self.format_bold)
        self.hearing_worksheet.write(row, 1, content)
        self.hearing_worksheet_active_row += 1

    def generate_hearing_worksheet(self):
        self.hearing_worksheet.set_column('A:A', 20)
        self.hearing_worksheet.set_column('B:B', 200)

        # add header to hearing worksheet
        self.hearing_worksheet.set_header(self.json['title'])

        self.add_hearing_row('Title', self.json['title'])
        self.add_hearing_row('Created', self.json['created_at'])
        self.add_hearing_row('Close', self.json['close_at'])
        # self.add_hearing_row('Author', self.json['created_by'])
        self.add_hearing_row('Abstract', self.json['abstract'])
        self.add_hearing_row('Borough', self.json['borough'])
        self.add_hearing_row('Labels', str('%s' % ', '.join(label for label in self.json['labels'])))
        self.add_hearing_row('Comments', str(self.json['n_comments']))
        self.add_hearing_row('Sections', str(len(self.json['sections'])))

    def add_comment_row(self, commented_type, title, comment):
        row = self.comments_worksheet_active_row
        # add title
        self.comments_worksheet.write(row, 0, title)
        # add type
        self.comments_worksheet.write(row, 1, commented_type)
        # add author
        self.comments_worksheet.write(row, 2, format_user_dict(comment['created_by']))
        # add creation date
        self.comments_worksheet.write(row, 3, comment['created_at'])
        # add votes
        self.comments_worksheet.write(row, 4, comment['n_votes'])
        # add content
        self.comments_worksheet.write(row, 5, comment['content'])
        self.comments_worksheet_active_row += 1

    def generate_comments_worksheet(self):
        self.comments_worksheet.set_column('A:A', 30)
        self.comments_worksheet.set_column('C:C', 20)
        self.comments_worksheet.set_column('D:D', 25)
        self.comments_worksheet.set_column('E:E', 5)
        self.comments_worksheet.set_column('F:F', 200)

        self.comments_worksheet.set_header('Comments of %s' % self.json['title'])

        self.comments_worksheet.write(0, 0, 'Title', self.format_bold)
        self.comments_worksheet.write(0, 1, 'Type', self.format_bold)
        self.comments_worksheet.write(0, 2, 'Author', self.format_bold)
        self.comments_worksheet.write(0, 3, 'Created', self.format_bold)
        self.comments_worksheet.write(0, 4, 'Votes', self.format_bold)
        self.comments_worksheet.write(0, 5, 'Content', self.format_bold)

        self.comments_worksheet_active_row = 1

        comments_count = 0

        for comment in self.json['comments']:
            self.add_comment_row('Hearing', self.json['title'], comment)
            comments_count += 1

        sections = [s for s in self.json['sections']]
        for s in sections:
            comments = [SectionCommentSerializer(c).data for c in SectionComment.objects.filter(section=s['id'])]
            for comment in comments:
                self.add_comment_row('Section', s['title'], comment)
                comments_count += 1

        self.add_hearing_row('All comments', str(comments_count))

    def get_xlsx(self):
        self.generate_hearing_worksheet()
        self.generate_comments_worksheet()
        self.xlsdoc.close()

        return self.buffer.getvalue()

    def get_response(self):
        response = HttpResponse(
            self.get_xlsx(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename={filename}.xlsx'.format(filename=self.json['title'])
        return response

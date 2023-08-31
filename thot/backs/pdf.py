# latex -- Thot latex back-end
# Copyright (C) 2009  <hugues.casse@laposte.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import thot.backs.latex as latex

def output(doc):
	doc.setVar("OUTPUT", "pdf")
	latex.output(doc)

__short__ = "PDF production based on Latex document."
__description__ = """Generates PDF document based on the latex backend.

There is use the same variables:
""" + latex.__vars__

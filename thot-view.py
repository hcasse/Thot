#!/usr/bin/python3
# thot.py -- Deprecated Thot entry point.
# Copyright (C) 2023  <hug.casse@gmail.com>
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

import os
import os.path

dir = os.path.abspath(os.path.dirname(__file__))
os.putenv("PYTHONPATH",
	os.getenv("PYTHONPATH", "") + ":" + dir)
import thot.view
thot.view.main()

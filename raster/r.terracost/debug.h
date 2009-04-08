/* 

   Copyright (C) 2006 Thomas Hazel, Laura Toma, Jan Vahrenhold and
   Rajiv Wickremesinghe

   This program is free software; you can redistribute it and/or
   modify it under the terms of the GNU General Public License as
   published by the Free Software Foundation; either version 2 of the
   License, or (at your option) any later version.

   This program is distributed in the hope that it will be useful, but
   WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
   General Public License for more details.

*/

#include <ostream>

#include "common.h"
#include "input.h"


template<class T>
void
dump_file(const char *strname, const char *outfile, const T &dummy) {
  AMI_STREAM<T> *str;

  str = new AMI_STREAM<T>(strname, AMI_READ_STREAM);   
  str->persist(PERSIST_PERSISTENT);

  ofstream os(outfile);

  cerr << "dumping " << strname << " to " << outfile << endl;

  T* item;
  AMI_err err;
  while((err = str->read_item(&item)) == AMI_ERROR_NO_ERROR) {
    os << *item << endl;
  }

  os.close();
  delete str;
}

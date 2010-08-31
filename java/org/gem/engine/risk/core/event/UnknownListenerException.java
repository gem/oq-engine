/*
 * [COPYRIGHT]
 *
 * [NAME] is free software; you can redistribute it and/or modify it
 * under the terms of the GNU Lesser General Public License as
 * published by the Free Software Foundation; either version 2.1 of
 * the License, or (at your option) any later version.
 *
 * This software is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this software; if not, write to the Free
 * Software Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA
 * 02110-1301 USA, or see the FSF site: http://www.fsf.org.
 */

package org.gem.engine.risk.core.event;

/**
 * Raised when a client is trying to lookup an unknown listener.
 * 
 * @author Andrea Cerisara
 * @version $Id: UnknownListenerException.java 546 2010-07-09 08:40:15Z acerisara $
 */
public class UnknownListenerException extends RuntimeException
{

    private static final long serialVersionUID = 8086958455313572509L;

    private final EventListener listener;

    /**
     * @param listener the listener used in the lookup process
     */
    public UnknownListenerException(EventListener listener)
    {
        this.listener = listener;
    }

    @Override
    public String getMessage()
    {
        return "Listener " + listener + " is not registered for any registered event.";
    }

}
